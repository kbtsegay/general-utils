"""
Real-time speech-to-text dictation tools.
"""

import os

# Suppress tokenizers parallelism warning when using threads
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import logging
import threading
import tempfile
import wave
import time
from argparse import _SubParsersAction
from pathlib import Path
from typing import Optional, List, Any

import numpy as np
import sounddevice as sd
from pynput import keyboard
from pynput.keyboard import Key, Controller

from gutils.core import Config

logger = logging.getLogger(__name__)

# Audio settings
SAMPLE_RATE = 16000  # Whisper expects 16kHz
CHANNELS = 1


def register_commands(subparsers: _SubParsersAction) -> None:
    """
    Register dictation subcommands.
    """
    dictation_parser = subparsers.add_parser(
        "dictation",
        help="Real-time speech-to-text dictation",
        description="Hold a hotkey to speak, release to transcribe and type",
    )

    dictation_subparsers = dictation_parser.add_subparsers(
        title="dictation commands",
        description="Available dictation operations",
        dest="dictation_command",
        required=True,
    )

    # Start command
    start_parser = dictation_subparsers.add_parser(
        "start",
        help="Start dictation daemon",
        description="Start real-time dictation with hotkey activation",
    )

    start_parser.add_argument(
        "--daemon",
        action="store_true",
        help="Run in daemon mode (currently same as normal mode)",
    )

    start_parser.set_defaults(func=execute_start)


def execute_start(args: Any, config: Config) -> int:
    """
    Execute the start dictation command.
    """
    logger.info("=" * 50)
    logger.info("         GUTILS DICTATION")
    logger.info("   Free, Private, Local Speech-to-Text")
    logger.info("=" * 50)
    logger.info("")

    check_permissions()

    try:
        whispr = WhisprDictation(config)
        whispr.run()
        return 0

    except KeyboardInterrupt:
        logger.info("\nGoodbye!")
        return 0

    except Exception as e:
        logger.error(f"Error: {e}")
        logger.error("If you see permission errors, make sure to grant accessibility access.")
        return 1


class WhisprDictation:
    """Real-time dictation using Whisper and optional LLM."""

    def __init__(self, config: Config):
        """
        Initialize dictation engine.
        """
        self.config = config
        self.recording = False
        self.audio_data: List[np.ndarray] = []
        self.keyboard_controller = Controller()
        self.whisper_model = None
        self.llm_model = None
        self.llm_tokenizer = None
        self.stream = None

        # Get configuration
        self.trigger_key_name = config.get("trigger_key", "alt")
        self.trigger_key = self._parse_trigger_key(self.trigger_key_name)
        self.whisper_model_name = config.get("whisper_model", "base")
        self.llm_model_name = config.get("llm_model", None)

        # Load vocabulary
        vocab_file = Path(config.get("vocab_file", str(Path.home() / ".gutils" / "vocab.txt")))
        self.vocabulary = self._load_vocabulary(vocab_file)

        logger.info("Loading models... (this may take a moment on first run)")
        self._load_whisper()
        if self.llm_model_name:
            self._load_llm()

        logger.info(
            f"Hold [{self._key_display_name(self.trigger_key)}] to speak, release to transcribe"
        )
        logger.info("Press Ctrl+C to exit")

    def _parse_trigger_key(self, key_name: str) -> Key:
        """Parse trigger key name to Key object."""
        key_map = {
            "alt": Key.alt,
            "alt_l": Key.alt_l,
            "alt_r": Key.alt_r,
            "ctrl": Key.ctrl,
            "ctrl_l": Key.ctrl_l,
            "ctrl_r": Key.ctrl_r,
            "cmd": Key.cmd,
            "cmd_l": Key.cmd_l,
            "cmd_r": Key.cmd_r,
            "shift_r": Key.shift_r,
        }
        return key_map.get(key_name.lower(), Key.alt)

    def _key_display_name(self, key: Key) -> str:
        """Get human-readable key name."""
        names = {
            Key.alt_r: "Right Option",
            Key.alt: "Left Option",
            Key.alt_l: "Left Option",
            Key.ctrl_r: "Right Control",
            Key.ctrl: "Left Control",
            Key.ctrl_l: "Left Control",
            Key.cmd_r: "Right Command",
            Key.cmd: "Left Command",
            Key.cmd_l: "Left Command",
            Key.shift_r: "Right Shift",
        }
        return names.get(key, str(key))

    def _load_vocabulary(self, vocab_file: Path) -> List[str]:
        """Load personal vocabulary from file."""
        if vocab_file.exists():
            try:
                vocab = [
                    line.strip() for line in vocab_file.read_text().splitlines() if line.strip()
                ]
                if vocab:
                    logger.info(f"Loaded {len(vocab)} vocabulary terms from {vocab_file}")
                return vocab
            except Exception as e:
                logger.warning(f"Could not load vocabulary: {e}")
        return []

    def _load_whisper(self) -> None:
        """Load the Whisper model using MLX for Apple Silicon optimization."""
        import mlx_whisper

        self.whisper_model = mlx_whisper

        self.model_map = {
            "tiny": "mlx-community/whisper-tiny-mlx",
            "tiny.en": "mlx-community/whisper-tiny.en-mlx",
            "base": "mlx-community/whisper-base-mlx",
            "base.en": "mlx-community/whisper-base.en-mlx",
            "small": "mlx-community/whisper-small-mlx",
            "small.en": "mlx-community/whisper-small.en-mlx",
            "medium": "mlx-community/whisper-medium-mlx",
            "medium.en": "mlx-community/whisper-medium.en-mlx",
            "large": "mlx-community/whisper-large-v3-mlx",
        }

        # Determine the full repository name
        # Default to small (en-mlx preferred)
        model_key = self.whisper_model_name

        # Determine the model name
        if model_key == "large":
            model_name = self.model_map["large"]
        elif f"{model_key}.en" in self.model_map:
            model_name = self.model_map[f"{model_key}.en"]
        elif model_key in self.model_map:
            model_name = self.model_map[model_key]
        else:
            # Strict validation - no silent fallback
            valid_models = sorted(list(set(k.replace(".en", "") for k in self.model_map.keys())))
            raise ValueError(f"Invalid whisper model '{model_key}'. Choose from: {valid_models}")

        self.full_model_name = model_name
        logger.info(f"Whisper '{self.whisper_model_name}' ({model_name}) loaded")

    def _load_llm(self) -> None:
        """Load the LLM model for post-processing."""
        from mlx_lm import load

        logger.info(f"Loading LLM '{self.llm_model_name}'...")
        self.llm_model, self.llm_tokenizer = load(self.llm_model_name)
        logger.info("LLM loaded")

    def _build_llm_prompt(self, raw_text: str) -> str:
        """Build the prompt for LLM post-processing."""
        vocab_context = ""
        if self.vocabulary:
            vocab_context = f"\n\nUse these exact spellings when these terms appear: {', '.join(self.vocabulary)}"

        return f"""You are a transcription editor. Your job is to clean up speech-to-text output.

Rules:
1. Keep ALL words - do not remove or summarize anything
2. Fix misheard words (e.g., "committee" -> "commit" if talking about git)
3. Add proper punctuation and capitalization
4. Output ONLY the corrected text, nothing else{vocab_context}

Input: {raw_text}
Output:"""

    def _post_process_with_llm(self, raw_text: str) -> str:
        """Clean up transcription using LLM."""
        if not self.llm_model:
            return raw_text

        from mlx_lm import generate

        prompt = self._build_llm_prompt(raw_text)

        messages = [{"role": "user", "content": prompt}]
        formatted_prompt = self.llm_tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )

        response = generate(
            self.llm_model,
            self.llm_tokenizer,
            prompt=formatted_prompt,
            max_tokens=max(200, len(raw_text.split()) * 2 + 100),
            verbose=False,
        )

        cleaned = response.strip()
        if cleaned.startswith('"') and cleaned.endswith('"'):
            cleaned = cleaned[1:-1]
        if cleaned.startswith("'") and cleaned.endswith("'"):
            cleaned = cleaned[1:-1]

        return cleaned if cleaned else raw_text

    def _audio_callback(self, indata: np.ndarray, frames: int, time_info: Any, status: Any) -> None:
        """Called for each audio block while recording."""
        if status:
            logger.debug(f"Audio status: {status}")
        if self.recording:
            self.audio_data.append(indata.copy())

    def start_recording(self) -> None:
        """Start recording audio from microphone."""
        if self.recording:
            return

        self.recording = True
        self.audio_data = []

        logger.info("Recording...")

        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype=np.float32,
            callback=self._audio_callback,
        )
        self.stream.start()

    def stop_recording_and_transcribe(self) -> None:
        """Stop recording, transcribe, and type the result."""
        if not self.recording:
            return

        self.recording = False

        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

        logger.info("Stopped recording")

        if not self.audio_data:
            logger.info("No audio captured")
            return

        audio = np.concatenate(self.audio_data, axis=0).flatten()
        duration = len(audio) / SAMPLE_RATE
        if duration < 0.3:
            logger.info("Recording too short")
            return

        logger.info(f"Transcribing {duration:.1f}s of audio...")

        temp_path: Optional[str] = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
                temp_path = tmp_file.name
                with wave.open(temp_path, "wb") as wav_file:
                    wav_file.setnchannels(CHANNELS)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(SAMPLE_RATE)
                    audio_int16 = (audio * 32767).astype(np.int16)
                    wav_file.writeframes(audio_int16.tobytes())

            initial_prompt = None
            if self.vocabulary:
                initial_prompt = ", ".join(self.vocabulary[:50])

            result = self.whisper_model.transcribe(
                temp_path,
                path_or_hf_repo=self.full_model_name,
                language="en",
                initial_prompt=initial_prompt,
            )

            raw_text = result.get("text", "").strip()

            if not raw_text:
                logger.info("No speech detected")
                return

            if self.llm_model:
                logger.debug(f'Raw: "{raw_text}"')
                text = self._post_process_with_llm(raw_text)
            else:
                text = raw_text

            logger.info(f'Detected: "{text}"')
            self._type_text(text)

        except Exception as e:
            logger.error(f"Transcription error: {e}")
        finally:
            if temp_path:
                Path(temp_path).unlink(missing_ok=True)

    def _type_text(self, text: str) -> None:
        """Type the transcribed text at current cursor position."""
        time.sleep(0.05)
        for char in text:
            self.keyboard_controller.type(char)
            time.sleep(0.005)

    def on_press(self, key: Key) -> None:
        """Handle key press."""
        if key == self.trigger_key:
            self.start_recording()

    def on_release(self, key: Key) -> None:
        """Handle key release."""
        if key == self.trigger_key:
            threading.Thread(target=self.stop_recording_and_transcribe).start()

    def run(self) -> None:
        """Start the hotkey listener."""
        with keyboard.Listener(on_press=self.on_press, on_release=self.on_release) as listener:
            listener.join()


def check_permissions() -> None:
    """Check and guide for macOS accessibility permissions."""
    import platform

    if platform.system() == "Darwin":
        logger.info("=" * 60)
        logger.info("macOS PERMISSIONS REQUIRED")
        logger.info("=" * 60)
        logger.info("")
        logger.info("This app needs Accessibility permissions to:")
        logger.info("  1. Detect global hotkeys")
        logger.info("  2. Type text in other apps")
        logger.info("")
        logger.info("Go to: System Settings -> Privacy & Security -> Accessibility")
        logger.info("  Add and enable 'Terminal' (or your terminal app)")
        logger.info("")
        logger.info("Also check: Privacy & Security -> Microphone")
        logger.info("  Ensure your terminal has microphone access")
        logger.info("=" * 60)
        logger.info("")

"""
Audio transcription tools using OpenAI Whisper or MLX Whisper.
"""

import sys
import logging
import tempfile
import json
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Any, Dict, Literal, Optional

from gutils.core import Config, smart_output

logger = logging.getLogger(__name__)

Backend = Literal["openai", "mlx"]
OutputFormat = Literal["txt", "json"]


def register_commands(subparsers: _SubParsersAction) -> None:
    """
    Register audio subcommands.
    """
    audio_parser = subparsers.add_parser(
        "audio",
        help="Audio transcription tools",
        description="Transcribe audio files to text using Whisper",
    )

    audio_subparsers = audio_parser.add_subparsers(
        title="audio commands",
        description="Available audio operations",
        dest="audio_command",
        required=True,
    )

    # Transcribe command
    transcribe_parser = audio_subparsers.add_parser(
        "transcribe",
        help="Transcribe audio to text",
        description="Transcribe audio files using OpenAI Whisper or MLX Whisper",
    )

    transcribe_parser.add_argument(
        "input",
        type=str,
        help="Audio file path or '-' to read from stdin",
    )

    transcribe_parser.add_argument(
        "--backend",
        type=str,
        choices=["mlx", "openai"],
        default=None,
        help="Whisper backend to use (default: from config or 'mlx')",
    )

    transcribe_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model size: tiny, base, small, medium, large (default: from config or 'base')",
    )

    transcribe_parser.add_argument(
        "--output-format",
        type=str,
        choices=["txt", "json"],
        default="txt",
        help="Output format (default: txt)",
    )

    transcribe_parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="FILE",
        help="Output file path (default: stdout)",
    )

    transcribe_parser.add_argument(
        "--language",
        type=str,
        help="Language code (e.g., 'en' for English) or auto-detect if not specified",
    )

    transcribe_parser.set_defaults(func=execute_transcribe)


def execute_transcribe(args: Any, config: Config) -> int:
    """
    Execute the transcribe command.
    """
    try:
        # Handle stdin input
        input_file = args.input
        temp_file = None

        if input_file == "-":
            # Read from stdin and save to temporary file
            logger.info("Reading audio data from stdin...")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
            temp_file.write(sys.stdin.buffer.read())
            temp_file.close()
            input_file = temp_file.name
            logger.info(f"Saved stdin to temporary file: {input_file}")

        # Get configuration
        backend = args.backend or config.get("whisper_backend", "mlx")
        model = args.model or config.get("whisper_model", "base")

        # Override output format if --json flag was set globally
        output_format = "json" if config.get("json_output") else args.output_format

        # Transcribe
        result = transcribe_audio(
            file_path=input_file,
            backend=backend,
            model=model,
            output_format=output_format,
            language=args.language,
        )

        # Format output
        output_text = format_output(result, output_format)

        # Output handling
        if args.output:
            # Save to file
            output_path = Path(args.output)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding="utf-8")
            logger.info(f"Transcription saved to: {args.output}")
        else:
            # Write to stdout
            smart_output(output_text)

        # Clean up temporary file if created
        if temp_file:
            Path(temp_file.name).unlink(missing_ok=True)

        return 0

    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return 1


def transcribe_audio(
    file_path: str,
    backend: Backend = "mlx",
    model: str = "base",
    language: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Transcribe audio file using Whisper.
    """
    # Validate file exists
    audio_file = Path(file_path)
    if not audio_file.exists():
        raise FileNotFoundError(f"Audio file not found: {file_path}")

    logger.info(f"Transcribing {file_path} using {backend} backend with model {model}")

    try:
        if backend == "mlx":
            result = _transcribe_mlx(file_path, model, language)
        elif backend == "openai":
            result = _transcribe_openai(file_path, model, language)
        else:
            raise ValueError(f"Unknown backend: {backend}")

        logger.info("Transcription completed successfully")
        return result

    except ImportError as e:
        raise ImportError(
            f"Backend '{backend}' not available. "
            f"Install required package: pip install {'mlx-whisper' if backend == 'mlx' else 'openai-whisper'}"
        ) from e
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        raise RuntimeError(f"Transcription failed: {e}") from e


def _transcribe_mlx(
    file_path: str,
    model: str,
    language: Optional[str],
) -> Dict[str, Any]:
    """Transcribe using MLX Whisper (optimized for Apple Silicon)."""
    import mlx_whisper

    # Map model names to MLX Hub repository names
    model_map = {
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

    # Use English-only model by default for better performance
    if language == "en" and f"{model}.en" in model_map:
        model_name = model_map[f"{model}.en"]
    else:
        model_name = model_map.get(model, model_map["base"])

    result = mlx_whisper.transcribe(
        file_path,
        path_or_hf_repo=model_name,
        language=language,
    )

    return {
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", []),
        "language": result.get("language", language),
    }


def _transcribe_openai(
    file_path: str,
    model: str,
    language: Optional[str],
) -> Dict[str, Any]:
    """Transcribe using OpenAI Whisper (CPU/GPU)."""
    import whisper
    import torch

    # Determine device
    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    logger.info(f"Using device: {device}")

    # Load model
    whisper_model = whisper.load_model(model, device=device)

    # Transcribe
    transcribe_options = {}
    if language:
        transcribe_options["language"] = language

    result = whisper_model.transcribe(file_path, **transcribe_options)

    return {
        "text": result.get("text", "").strip(),
        "segments": result.get("segments", []),
        "language": result.get("language", language),
    }


def format_output(result: Dict[str, Any], output_format: OutputFormat) -> str:
    """
    Format transcription result for output.
    """
    if output_format == "json":
        return json.dumps(result, indent=2, ensure_ascii=False)
    else:
        # Plain text format
        return result["text"]

#!/usr/bin/env python3

import sys
import os
from pathlib import Path
import mlx_whisper

# --- CONFIG ---
MODEL_NAME = "mlx-community/whisper-base.en-mlx"  # English-only base model
OUTPUT_DIR = "outputs"

def transcribe_file(file_path):
    """Transcribe a single file using mlx_whisper."""
    print(f"Transcribing: {file_path}\n")
    result = mlx_whisper.transcribe(file_path, path_or_hf_repo=MODEL_NAME)
    text = result.get("text", "").strip()
    return text

def main():
    if len(sys.argv) < 2:
        print("Usage: transcribe-faster <path_to_mp3>")
        sys.exit(1)

    file_path = os.path.abspath(sys.argv[1])
    transcription = transcribe_file(file_path)

    # Save output
    output_path = Path(OUTPUT_DIR)
    output_path.mkdir(exist_ok=True)
    txt_file = output_path / f"{Path(file_path).stem}.txt"
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(transcription)

    print("\nTranscription:\n")
    print(transcription)
    print(f"\nTranscription saved to: {txt_file}")

if __name__ == "__main__":
    main()

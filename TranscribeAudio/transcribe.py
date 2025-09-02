#!/usr/bin/env python3

import sys
import os
import whisper
import torch

def transcribe_mp3(file_path: str):
    device = "cpu"

    # Load the base Whisper model on the selected device
    model = whisper.load_model("base").to(device)

    # Transcribe audio
    result = model.transcribe(file_path, language="en")
    text = result['text'].strip()

    print("\nTranscription:\n")
    print(text)

    # Create outputs folder if it doesn't exist
    output_dir = os.path.join(os.path.dirname(__file__), "outputs")
    os.makedirs(output_dir, exist_ok=True)

    # Save transcription as a .txt file with same base name as audio
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    txt_file = os.path.join(output_dir, f"{base_name}.txt")
    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"\nTranscription saved to: {txt_file}")
    return text

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: transcribe <path_to_mp3>")
        sys.exit(1)

    mp3_file = sys.argv[1]

    try:
        transcribe_mp3(mp3_file)
    except Exception as e:
        print(f"Error during transcription: {e}")
        sys.exit(1)


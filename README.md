# G-Utils 🛠️

A unified CLI suite of powerful utility tools for macOS productivity.

## 🚀 Features

### YouTube Download

Download and convert YouTube videos to MP3 audio files with pipe support for composability.

### Audio Transcription

Convert audio files to text using OpenAI's Whisper with MLX acceleration for Apple Silicon. Supports multiple backends, JSON output with timestamps, and stdin piping.

### PDF Processing

Extract text from PDF files using direct parsing or OCR technology. Includes metadata extraction and multiple output formats.

### QR Code Generation

Generate customizable QR codes with multiple styles, custom colors, and various output formats.

### AI Image Generation

Generate AI-powered images using Google's Gemini API with configurable aspect ratios and quality settings.

### Real-time Dictation

Local speech-to-text with hotkey activation, optional LLM post-processing, and personal vocabulary support.

## 📋 Prerequisites

- Python 3.8+
- macOS (optimized for Apple Silicon)
- ffmpeg (for audio processing)
- tesseract (for OCR functionality)
- Google AI Studio API key (for AI image generation)

## 🔧 Installation

1. Clone the repository:

```bash
git clone https://github.com/kalebtsegay/general-utils.git
cd general-utils
```

2. Install the package:

```bash
pip install -e .
```

3. Install system dependencies:

```bash
brew install ffmpeg tesseract
```

4. (Optional) Set up configuration:

```bash
mkdir -p ~/.gutils
cp config.yaml.example ~/.gutils/config.yaml
# Edit ~/.gutils/config.yaml with your preferences
```

## 📖 Usage

### General Command Structure

```bash
gutils [--json] [--verbose] [--config PATH] <command> <subcommand> [options]
```

### Global Flags

- `--json`: Force JSON output (machine-readable)
- `--verbose`, `-v`: Enable verbose logging
- `--config PATH`: Use custom config file

### YouTube Download

```bash
# Download video as MP3 (default)
gutils tube download "https://youtube.com/watch?v=VIDEO_ID"

# Download video (not just audio)
gutils tube download "URL" --video

# Pipe output for composability
gutils tube download "URL" --pipe | gutils audio transcribe -
```

### Audio Transcription

```bash
# Basic transcription
gutils audio transcribe audio.mp3

# Use MLX backend (faster on Apple Silicon)
gutils audio transcribe audio.mp3 --backend mlx --model small

# Output to JSON with timestamps
gutils audio transcribe audio.mp3 --output-format json

# Transcribe from stdin (for piping)
cat audio.mp3 | gutils audio transcribe -

# Save to specific file
gutils audio transcribe audio.mp3 -o transcript.txt
```

### PDF Text Extraction

```bash
# Direct text extraction
gutils pdf extract document.pdf

# Force OCR for scanned PDFs
gutils pdf extract scanned.pdf --method ocr

# Output to file with metadata
gutils pdf extract document.pdf -o output.txt --metadata

# JSON format
gutils pdf extract document.pdf --format json

# Extract metadata only
gutils pdf meta document.pdf
```

### QR Code Generation

```bash
# Basic QR code
gutils image qr "https://example.com"

# Custom output path
gutils image qr "https://example.com" -o my_qr.png

# Rounded style with custom colors
gutils image qr "https://example.com" --style rounded --fill-color blue --back-color white

# Larger size with custom border
gutils image qr "https://example.com" --size 15 --border 2
```

### AI Image Generation

```bash
# Set API key first
export GEMINI_API_KEY='your-api-key-here'  # Get from https://aistudio.google.com/apikey

# Basic image generation
gutils image generate "A serene mountain landscape at sunset"

# Generate multiple images
gutils image generate "Abstract art" --num-images 4

# Custom aspect ratio
gutils image generate "Minimalist design" --aspect-ratio 9:16

# Save to specific file
gutils image generate "A cute robot" -o my_robot.png

# Use higher quality model
gutils image generate "Photorealistic portrait" --model gemini-3-pro-image-preview
```

### Real-time Dictation

```bash
# Start dictation daemon
gutils dictation start

# Hold the configured hotkey (default: Left Option) to speak
# Release to transcribe and type
```

## 🔗 Composability

G-Utils tools are designed to work together following Unix philosophy:

```bash
# Download YouTube video and transcribe it
gutils tube download "https://youtube.com/watch?v=VIDEO_ID" --pipe | gutils audio transcribe - --json

# Extract PDF text and save to file
gutils pdf extract document.pdf > output.txt

# Generate QR code for a URL
echo "https://example.com" | xargs gutils image qr
```

## ⚙️ Configuration

Create `~/.gutils/config.yaml` to customize settings:

```yaml
# General settings
output_dir: "outputs"
log_level: "INFO"

# Audio transcription
whisper_model: "base"
whisper_backend: "mlx"

# Dictation
trigger_key: "alt"
llm_model: false
vocab_file: "~/.gutils/vocab.txt"

# API keys
gemini_api_key: "your-key-here"
```

You can also use environment variables:

```bash
export GUTILS_WHISPER_MODEL=small
export GUTILS_OUTPUT_DIR=~/Documents/outputs
export GEMINI_API_KEY=your-key-here
```

## 📁 Project Structure

```
general-utils/
├── gutils/                # Main package
│   ├── core/              # Shared utilities (logging, config, I/O)
│   ├── audio.py           # Audio transcription
│   ├── tube.py            # YouTube download
│   ├── pdf.py             # PDF processing
│   ├── image.py           # QR & AI image generation
│   ├── dictation.py       # Real-time dictation
│   └── main.py            # CLI entry point
├── pyproject.toml         # Package configuration
├── config.yaml.example    # Example configuration
└── outputs/               # Default output directory
```

## 🤝 Contributing

Feel free to open issues or submit pull requests with improvements!

## 📄 License

MIT License - see LICENSE file for details

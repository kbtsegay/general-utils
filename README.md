# General Utils 🛠️

A collection of powerful utility tools to enhance productivity on macOS.

## 🚀 Features

### TranscribeAudio
Convert audio files to text using OpenAI's Whisper model with MLX acceleration for Apple Silicon.
- `transcribe.py` - Standard transcription
- `transcribe_faster.py` - Optimized version for faster processing

### Youtube2MP3
Download and convert YouTube videos to MP3 audio files.
- `convert.py` - YouTube to MP3 converter using yt-dlp

## 📋 Prerequisites

- Python 3.8+
- macOS (optimized for Apple Silicon)
- ffmpeg (for audio processing)

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/general-utils.git
cd general-utils
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ffmpeg (if not already installed):
```bash
brew install ffmpeg
```

## 📖 Usage

### Transcribe Audio
```bash
cd TranscribeAudio
python transcribe.py input_audio.mp3
# or for faster processing:
python transcribe_faster.py input_audio.mp3
```

### YouTube to MP3
```bash
cd Youtube2MP3
python convert.py "https://youtube.com/watch?v=VIDEO_ID"
```

## 📁 Project Structure
```
general-utils/
├── TranscribeAudio/    # Audio transcription tools
│   ├── transcribe.py
│   ├── transcribe_faster.py
│   └── outputs/        # Transcription results
├── Youtube2MP3/        # YouTube conversion tools
│   └── convert.py
└── outputs/            # General output directory
```

## 🤝 Contributing

Feel free to open issues or submit pull requests with improvements!

## 📄 License

MIT License - see LICENSE file for details

## 🔮 Future Enhancements

- [ ] Add batch processing support
- [ ] Create CLI interface for all tools
- [ ] Add configuration file support
- [ ] Implement progress bars
- [ ] Add more audio/video formats support
- [ ] Create web interface
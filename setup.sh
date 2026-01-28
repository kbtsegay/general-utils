#!/bin/bash

# Setup script for G-Utils
# Modern installation using pip

echo "🔧 Setting up G-Utils..."
echo ""

# Get the directory where this script is located
UTILS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if we're in a virtual environment
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Warning: You're not in a virtual environment."
    echo "   Consider creating one with: python3 -m venv venv && source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Install the package in editable mode
echo "📦 Installing G-Utils package..."
pip install -e "$UTILS_DIR"

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Installation successful!"
    echo ""
    echo "🚀 You can now use the 'gutils' command:"
    echo "   gutils --help"
    echo ""
    echo "Examples:"
    echo "   gutils tube download \"https://youtube.com/watch?v=...\" --audio-only"
    echo "   gutils audio transcribe audio.mp3 --output-format json"
    echo "   gutils pdf extract document.pdf"
    echo "   gutils image qr \"https://example.com\""
    echo "   gutils image generate \"A serene landscape\""
    echo "   gutils dictation start"
    echo ""
    echo "📖 For more info, see README.md or run: gutils <command> --help"
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
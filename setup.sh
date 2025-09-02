#!/bin/bash

# Setup script for general-utils
# Makes Python scripts executable and sets up aliases

echo "🔧 Setting up general-utils..."

# Get the directory where this script is located
UTILS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Make Python scripts executable
echo "📝 Making scripts executable..."
chmod +x "$UTILS_DIR/Youtube2MP3/convert.py"
chmod +x "$UTILS_DIR/TranscribeAudio/transcribe.py"
chmod +x "$UTILS_DIR/TranscribeAudio/transcribe_faster.py"

# Add shebang to Python files if not present
for file in "$UTILS_DIR/Youtube2MP3/convert.py" "$UTILS_DIR/TranscribeAudio/transcribe.py" "$UTILS_DIR/TranscribeAudio/transcribe_faster.py"; do
    if ! head -n 1 "$file" | grep -q "^#!/usr/bin/env python"; then
        echo "Adding shebang to $(basename $file)..."
        echo '#!/usr/bin/env python3' | cat - "$file" > temp && mv temp "$file"
    fi
done

echo "✅ Scripts are now executable!"
echo ""
echo "📌 Add these aliases to your ~/.zshrc or ~/.bashrc:"
echo ""
echo "# General Utils Executables"
echo "alias yt2mp3=\"$UTILS_DIR/Youtube2MP3/convert.py\""
echo "alias transcribe=\"$UTILS_DIR/TranscribeAudio/transcribe.py\""
echo "alias transcribe-faster=\"$UTILS_DIR/TranscribeAudio/transcribe_faster.py\""
echo ""
echo "Then reload your shell configuration with: source ~/.zshrc"
echo ""
echo "🚀 Setup complete!"
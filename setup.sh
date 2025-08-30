#!/bin/bash

# YouTube Whisper Setup Script for Mac/Linux
# This script sets up the complete environment for audio transcription

echo "========================================"
echo "YouTube Whisper Transcription Setup"
echo "========================================"
echo ""

# Check Python installation
echo "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    echo "   Visit: https://www.python.org/downloads/"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✓ Python $PYTHON_VERSION found"
echo ""

# Check FFmpeg installation
echo "Checking FFmpeg installation..."
if ! command -v ffmpeg &> /dev/null; then
    echo "⚠️  FFmpeg is not installed. It's required for audio processing."
    echo ""
    echo "Install FFmpeg:"
    echo "  Mac:    brew install ffmpeg"
    echo "  Ubuntu: sudo apt-get install ffmpeg"
    echo "  CentOS: sudo yum install ffmpeg"
    echo ""
    read -p "Continue without FFmpeg? (y/n): " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
else
    echo "✓ FFmpeg found"
fi
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "⚠️  Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet flask openai yt-dlp pydub
echo "✓ Dependencies installed"
echo ""

# Check for OpenAI API key
echo "Checking OpenAI API key..."
if [ -z "$OPENAI_API_KEY" ]; then
    echo "⚠️  OPENAI_API_KEY is not set"
    echo ""
    echo "You need an OpenAI API key to use this application."
    echo "Get one at: https://platform.openai.com/api-keys"
    echo ""
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    
    if [ ! -z "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
        echo ""
        echo "To make this permanent, add to your ~/.bashrc or ~/.zshrc:"
        echo "  export OPENAI_API_KEY='$api_key'"
        echo ""
        echo "✓ API key set for this session"
    else
        echo ""
        echo "⚠️  Remember to set OPENAI_API_KEY before running the app:"
        echo "  export OPENAI_API_KEY='your-key-here'"
    fi
else
    echo "✓ OpenAI API key found"
fi
echo ""

# Create data directories
echo "Creating data directories..."
mkdir -p data/audio data/transcripts data/subtitles
echo "✓ Directories created"
echo ""

# Create run script
echo "Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash
source venv/bin/activate
python app.py
EOF
chmod +x run.sh
echo "✓ Run script created"
echo ""

echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "To start the application:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
echo "Then open your browser to: http://localhost:5000"
echo ""

# Ask if user wants to start now
read -p "Start the application now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Starting application..."
    python app.py
fi
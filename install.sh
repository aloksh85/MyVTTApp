#!/bin/bash
set -e

# Change to the script's directory
cd "$(dirname "$0")"

echo "=== Offline VTT App Setup ==="

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3."
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing base requirements..."
pip install sounddevice soundfile pynput pyperclip numpy PyQt6

# OS and Architecture Detection
OS="$(uname -s)"
ARCH="$(uname -m)"

echo "Detected OS: $OS"
echo "Detected Architecture: $ARCH"

# Install correct UI library
if [ "$OS" = "Darwin" ]; then
    echo "Installing macOS UI (rumps)..."
    pip install rumps
    # Also ensuring pystray is available for cross-compat tests
    pip install pystray
else
    echo "Installing Linux UI (pystray) and automation tools..."
    pip install pystray
    pip install pyautogui
    # Require xclip/xsel for pyperclip on Linux
    if command -v apt-get &> /dev/null; then
        echo "Installing xclip for clipboard support via apt..."
        sudo apt-get install -y xclip xdotool python3-tk python3-dev
    elif command -v pacman &> /dev/null; then
         echo "Installing xclip for clipboard support via pacman..."
         sudo pacman -S --noconfirm xclip xdotool tk python
    fi
fi

# Install correct Whisper backend
if [ "$OS" = "Darwin" ] && [ "$ARCH" = "arm64" ]; then
    echo "Apple Silicon Mac detected. Installing mlx-whisper for native performance..."
    pip install mlx-whisper huggingface_hub
    
    echo "Downloading and caching mlx-whisper model..."
    python3 -c "import mlx_whisper; import numpy as np; mlx_whisper.transcribe(np.zeros((16000), dtype=np.float32), path_or_hf_repo='mlx-community/whisper-base-mlx')"
    echo "mlx-whisper model cached successfully!"
else
    echo "Non-Apple Silicon or Linux detected. Installing faster-whisper..."
    pip install faster-whisper
    
    echo "Downloading and caching faster-whisper model..."
    python3 -c "from faster_whisper import WhisperModel; model = WhisperModel('base', device='cpu', compute_type='int8')"
    echo "faster-whisper model cached successfully!"
fi

echo ""
echo "=== Setup Complete ==="
echo "You can now run the app via:"
echo "  ./run.sh"

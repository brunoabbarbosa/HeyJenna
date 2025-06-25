#!/bin/bash

echo "Starting HeyJenna..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://python.org"
    exit 1
fi

# Check if virtual environment exists
if [ ! -f "env/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv env
    if [ $? -ne 0 ]; then
        echo "Error: Failed to create virtual environment"
        exit 1
    fi
fi

# Activate virtual environment
echo "Activating virtual environment..."
source env/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements"
    exit 1
fi

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Warning: FFmpeg not found in PATH"
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Or download from https://ffmpeg.org/download.html"
    echo
    read -p "Press Enter to continue anyway..."
fi

# Run the application
echo "Starting HeyJenna server..."
echo "Access the web interface at: http://localhost:5000"
echo "Press Ctrl+C to stop the server"
echo
python heyjenna.py 
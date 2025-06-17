#!/usr/bin/env python3
"""
Setup script for Jeff The Temp - Multi-Platform Video Downloader
"""

import os
import sys
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def install_requirements():
    """Install Python requirements"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Python dependencies installed successfully")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("\n🎵 Checking FFmpeg installation...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found")
        print_ffmpeg_instructions()
        return False

def print_ffmpeg_instructions():
    """Print FFmpeg installation instructions"""
    system = platform.system().lower()
    print("\n📋 FFmpeg Installation Instructions:")
    
    if system == "windows":
        print("  1. Download FFmpeg from: https://ffmpeg.org/download.html")
        print("  2. Extract the archive")
        print("  3. Add the 'bin' folder to your PATH environment variable")
        print("  4. Restart your command prompt/terminal")
    elif system == "darwin":  # macOS
        print("  Install using Homebrew:")
        print("    brew install ffmpeg")
        print("  Or download from: https://ffmpeg.org/download.html")
    else:  # Linux
        print("  Ubuntu/Debian:")
        print("    sudo apt update && sudo apt install ffmpeg")
        print("  CentOS/RHEL:")
        print("    sudo yum install ffmpeg")
        print("  Or download from: https://ffmpeg.org/download.html")

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["downloads", "subtitles"]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✅ Created directory: {directory}")
        else:
            print(f"✅ Directory exists: {directory}")

def print_cookie_instructions():
    """Print cookie setup instructions"""
    print("\n🍪 Cookie Setup (Optional):")
    print("  For authenticated downloads, you can add cookie files:")
    print("  - www.youtube.com_cookies.txt")
    print("  - www.tiktok.com_cookies.txt") 
    print("  - www.instagram.com_cookies.txt")
    print("  - www.facebook.com_cookies.txt")
    print("  ")
    print("  Use browser extensions like 'Get cookies.txt' to export cookies")

def main():
    """Main setup function"""
    print("🚀 Jeff The Temp - Setup Script")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        print("\n❌ Setup failed during dependency installation")
        sys.exit(1)
    
    # Check FFmpeg
    ffmpeg_ok = check_ffmpeg()
    
    # Create directories
    create_directories()
    
    # Print cookie instructions
    print_cookie_instructions()
    
    # Final instructions
    print("\n" + "=" * 40)
    if ffmpeg_ok:
        print("✅ Setup completed successfully!")
        print("\n🎯 Next steps:")
        print("  1. Run the application: python heyjeff.py")
        print("  2. Open your browser to: http://localhost:5000")
        print("  3. Start downloading videos!")
    else:
        print("⚠️  Setup completed with warnings!")
        print("\n🎯 Next steps:")
        print("  1. Install FFmpeg (see instructions above)")
        print("  2. Run the application: python heyjeff.py")
        print("  3. Open your browser to: http://localhost:5000")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
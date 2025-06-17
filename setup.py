#!/usr/bin/env python3
"""
Setup script for Jenna The Temp - Multi-Platform Video Downloader
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
    """Install required packages"""
    print("\n📦 Installing Python dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    print("\n🎬 Checking FFmpeg installation...")
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        print("✅ FFmpeg is installed")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ FFmpeg not found")
        print("\n📋 FFmpeg Installation Instructions:")
        
        system = platform.system().lower()
        if system == "windows":
            print("   Windows:")
            print("   1. Download from: https://ffmpeg.org/download.html")
            print("   2. Extract to a folder (e.g., C:\\ffmpeg)")
            print("   3. Add C:\\ffmpeg\\bin to your PATH environment variable")
        elif system == "darwin":
            print("   macOS:")
            print("   1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("   2. Run: brew install ffmpeg")
        else:
            print("   Linux:")
            print("   1. Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg")
            print("   2. CentOS/RHEL: sudo yum install ffmpeg")
            print("   3. Arch: sudo pacman -S ffmpeg")
        
        return False

def create_directories():
    """Create necessary directories"""
    print("\n📁 Creating directories...")
    directories = ["downloads", "subtitles"]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created {directory}/ directory")

def print_cookie_instructions():
    """Print cookie setup instructions"""
    print("\n🍪 Cookie Setup (Optional):")
    print("For authenticated downloads from private or age-restricted content:")
    print("1. Export cookies from your browser using extensions like 'Get cookies.txt'")
    print("2. Place cookie files in the project root with these names:")
    print("   - www.youtube.com_cookies.txt")
    print("   - www.tiktok.com_cookies.txt")
    print("   - www.instagram.com_cookies.txt")
    print("   - www.facebook.com_cookies.txt")

def main():
    """Main setup function"""
    print("🚀 Jenna The Temp - Setup Script")
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
        print("  1. Run the application: python heynjenna.py")
        print("  2. Open your browser to: http://localhost:5000")
        print("  3. Start downloading videos!")
    else:
        print("⚠️  Setup completed with warnings!")
        print("\n🎯 Next steps:")
        print("  1. Install FFmpeg (see instructions above)")
        print("  2. Run the application: python heynjenna.py")
        print("  3. Open your browser to: http://localhost:5000")
    
    print("\n📚 For more information, see README.md")

if __name__ == "__main__":
    main()
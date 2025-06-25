# HeyJenna

> HeyJenna is the temp that I always wanted, she doesn't do anything very quickly, sometimes I have to take a look because something is buggy but she is at least a little bit reliable. Thank you Jenna!

## Features

- **Multi-Platform Support**: Download videos from YouTube, TikTok, Instagram, Facebook, Reddit
- **Audio Transcription**: Automatic transcription using OpenAI Whisper
- **Translation**: Translate transcripts to multiple languages
- **File Management**: Organize, rename, and delete downloaded files
- **Web Interface**: Clean, responsive web UI with real-time progress
- **Cookie Support**: Authenticated downloads using browser cookies

## Screenshots

The application provides three main interfaces:
- **Download**: Paste video URLs and download with options for MP3-only and transcription
- **File Manager**: View, organize, and manage downloaded files with video previews
- **Transcribe**: Transcribe existing files and translate transcripts

## Requirements

- **Python 3.10.14** (other versions may not work correctly)
- **FFmpeg** (required for audio/video processing)
- Dependencies listed in `requirements.txt`
- **Cookie files** for some platforms (optional, for authenticated downloads)

## Quick Start

### Windows
1. **Download and extract** the project
2. **Double-click** `run.bat` to start the application
3. **Open your browser** and go to `http://localhost:5000`

### Linux/macOS
1. **Download and extract** the project
2. **Run** `./run.sh` in terminal
3. **Open your browser** and go to `http://localhost:5000`

## Manual Installation

1. **Clone the repository**
```bash
git clone https://github.com/brunoabbarbosa/HeyJenna.git
cd HeyJenna
```

2. **Create and activate a virtual environment**
```bash
python3.10 -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Install FFmpeg**
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

5. **Configure the application (optional)**
```bash
cp env.example .env
# Edit .env file with your preferred settings
```

6. **Run the application**
```bash
python heyjenna.py
```

7. **Access the web interface**
   - Open your browser and go to `http://localhost:5000`
   - For mobile access on same WiFi: `http://YOUR_COMPUTER_IP:5000`

## Usage

### Basic Video Download
1. Go to the Download page
2. Paste video URLs (one per line, up to 10)
3. Choose options:
   - **Transcribe**: Automatically transcribe audio after download
   - **MP3 Only**: Download audio only, skip video
4. Click "Download Videos"

### File Management
1. Go to "Sort Files" to view all downloaded files
2. Preview videos directly in the browser
3. Rename files by clicking on the filename
4. Delete files using the delete button

### Transcription & Translation
1. Go to "Transcribe" page
2. Select a downloaded file or existing transcript
3. Transcribe audio files using Whisper
4. Translate transcripts to different languages
5. Save or download the results

## Cookie Setup (Optional)

For authenticated downloads from private or age-restricted content:

1. **Export cookies** from your browser using extensions like "Get cookies.txt"
2. **Place cookie files** in the project root with these names:
   - `www.youtube.com_cookies.txt`
   - `www.tiktok.com_cookies.txt`
   - `www.instagram.com_cookies.txt`
   - `www.facebook.com_cookies.txt`
   - `www.reddit.com_cookies.txt`

## Configuration

### Environment Variables

You can configure the application using environment variables or a `.env` file:

```bash
# Copy the example environment file
cp env.example .env
# Edit .env with your preferred settings
```

Key configuration options:
- `WHISPER_MODEL`: Choose transcription model (tiny, base, small, medium, large)
- `MAX_LINKS_PER_REQUEST`: Maximum URLs to process at once (default: 10)
- `MAX_FILE_SIZE_MB`: Maximum file size limit (default: 500MB)
- `VIDEO_QUALITY`: Video quality preference for downloads
- `FLASK_HOST` and `FLASK_PORT`: Server host and port settings

### Directories

The application creates directories automatically:
- `downloads/` - Downloaded video/audio files
- `subtitles/` - Generated transcripts and translations
- `Translations/` - Translation files

## Supported Platforms

- **YouTube** (youtube.com, youtu.be)
- **TikTok** (tiktok.com)
- **Instagram** (instagram.com)
- **Facebook** (fb.watch)
- **Reddit** (reddit.com)

## File Naming Convention

Downloaded files follow this pattern:
`{PLATFORM}.{TITLE}.{UPLOADER}.{EXTENSION}`

Examples:
- `YT.Amazing.Video.Title.ChannelName.mp4`
- `TT.Funny.Dance.Video.username.mp4`
- `IG.Story.Video.username.mp4`

## Project Structure

```
heyjenna/
├── heyjenna.py              # Main Flask application
├── config.py                # Configuration settings
├── requirements.txt         # Python dependencies
├── README.md               # This file
├── LICENSE                 # MIT License
├── .gitignore             # Git ignore rules
├── run.bat                # Windows startup script
├── run.sh                 # Linux/macOS startup script
├── env.example            # Environment variables example
├── downloads/             # Downloaded video files (ignored)
├── subtitles/             # Generated transcripts (ignored)
├── Translations/          # Translation files (ignored)
├── templates/             # HTML templates
│   ├── index.html        # Main application interface
│   ├── dl.html           # Download page
│   ├── sort.html         # File management page
│   ├── transcribe.html   # Transcription page
│   └── console.html      # Console/logs page
└── static/               # Static assets
    └── SVG/              # SVG icons and logo
        ├── jenna.svg     # Main logo
        ├── download.svg  # Download icon
        ├── transcribe.svg # Transcribe icon
        └── sort.svg      # Sort icon
```

## Dependencies

- **Flask** - Web framework
- **yt-dlp** - Video downloading
- **openai-whisper** - Audio transcription
- **ffmpeg-python** - Audio/video processing
- **googletrans** - Translation services
- **requests** - HTTP requests
- **beautifulsoup4** - HTML parsing

## API Endpoints

- `POST /process` - Process video URLs
- `GET /file/<filename>` - Download files
- `POST /edit` - Transcribe uploaded files
- `POST /save_transcript` - Save transcripts

## Troubleshooting

### Common Issues

1. **FFmpeg not found**: Install FFmpeg and add it to your system PATH
2. **Python version issues**: Use Python 3.10.14 for best compatibility
3. **Permission errors**: Make sure you have write permissions in the project directory
4. **Port already in use**: Change the port in the configuration or kill the process using port 5000

### Windows Specific

- **WSL users**: The application automatically detects WSL and opens Windows Explorer correctly
- **Firewall**: Allow Python through Windows Firewall if prompted
- **Antivirus**: Some antivirus software may flag the application, add it to exclusions if needed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- **yt-dlp** for video downloading capabilities
- **OpenAI Whisper** for audio transcription
- **Flask** for the web framework
- **Tailwind CSS** for styling

---

If you have issues, check your cookies, Python version, and network setup. HeyJenna is reliable, but sometimes needs a little help!
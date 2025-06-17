# Jeff The Temp - Multi-Platform Video Downloader

A Flask-based web application for downloading and processing videos from multiple platforms including YouTube, TikTok, Instagram, and Facebook. Features include video downloading, audio transcription using OpenAI Whisper, and translation capabilities.

## Features

- **Multi-Platform Support**: Download videos from YouTube, TikTok, Instagram, Facebook
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

## Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd jeff-the-temp
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Install FFmpeg** (required for audio processing)
   - **Windows**: Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - **macOS**: `brew install ffmpeg`
   - **Linux**: `sudo apt install ffmpeg`

4. **Run the application**
```bash
python heyjeff.py
```

5. **Access the web interface**
   - Open your browser and go to `http://localhost:5000`

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

## Configuration

The application creates two directories automatically:
- `downloads/` - Downloaded video/audio files
- `subtitles/` - Generated transcripts and translations

## Supported Platforms

- **YouTube** (youtube.com, youtu.be)
- **TikTok** (tiktok.com)
- **Instagram** (instagram.com)
- **Facebook** (fb.watch)

## Dependencies

- **Flask** - Web framework
- **yt-dlp** - Video downloading
- **openai-whisper** - Audio transcription
- **ffmpeg-python** - Audio/video processing
- **googletrans** - Translation services

## File Naming Convention

Downloaded files follow this pattern:
`{PLATFORM}-{TITLE}.{UPLOADER}.{EXTENSION}`

Examples:
- `YT-Amazing.Video.Title.ChannelName.mp4`
- `TT-Funny.Dance.Video.username.mp4`
- `IG-Story.Video.username.mp4`

## API Endpoints

- `POST /download` - Download videos from URLs
- `GET /api/files` - Get list of downloaded files
- `POST /transcribe_file` - Transcribe a specific file
- `POST /translate` - Translate text
- `POST /rename` - Rename a file
- `POST /delete` - Delete a file

## Development

The project structure:
```
jeff-the-temp/
├── heyjeff.py              # Main Flask application
├── requirements.txt        # Python dependencies
├── templates/             # HTML templates
│   ├── dl.html           # Download page
│   ├── sort.html         # File management
│   ├── transcribe.html   # Transcription interface
│   └── console.html      # Debug console
├── downloads/            # Downloaded files (created automatically)
├── subtitles/           # Transcripts (created automatically)
└── *.txt                # Cookie files (optional)
```

## License

This project is open source. Feel free to modify and distribute.

## Troubleshooting

**Common Issues:**

1. **FFmpeg not found**: Make sure FFmpeg is installed and in your PATH
2. **Download fails**: Check if the video is available and not private
3. **Transcription slow**: Whisper processing is CPU-intensive, be patient
4. **Cookie issues**: Make sure cookie files are in the correct format

**Getting Help:**
- Check the browser console for JavaScript errors
- Look at the Flask console output for server errors
- Ensure all dependencies are properly installed

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

---

**Note**: This tool is for personal use and educational purposes. Respect the terms of service of the platforms you're downloading from.
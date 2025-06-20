from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify, Response
import os
import uuid
import whisper
import ffmpeg
from werkzeug.utils import secure_filename
from googletrans import Translator
import yt_dlp
import re
from config import get_config
import time
import traceback
import sys
import subprocess
import json
import requests
from bs4 import BeautifulSoup

app = Flask(__name__, static_folder='static')

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)
os.makedirs('static/SVG', exist_ok=True)
os.makedirs('Translations', exist_ok=True)

# Initialize Whisper model
print(f"Loading Whisper model: {app.config['WHISPER_MODEL']}")
model = whisper.load_model(app.config['WHISPER_MODEL'])
translator = Translator()

# Get cookie files from config
COOKIE_FILES = app.config['COOKIE_FILES']

# Console log storage
console_logs = []

class ConsoleLogger:
    def debug(self, msg):
        if msg.startswith('[debug]'):
            return
        log_to_console(f"[yt-dlp] {msg}")
    
    def warning(self, msg):
        log_to_console(f"[yt-dlp WARNING] {msg}")
    
    def error(self, msg):
        log_to_console(f"[yt-dlp ERROR] {msg}")

def log_to_console(message):
    """Add message to console logs"""
    timestamp = time.strftime("%H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    console_logs.append(log_entry)
    # Keep only last 1000 entries
    if len(console_logs) > 1000:
        console_logs.pop(0)

def get_cookies_file(url):
    """Get the appropriate cookies file for a URL"""
    for domain, cookie_file in COOKIE_FILES.items():
        if domain in url.lower():
            if os.path.exists(cookie_file):
                return cookie_file
    return None

def detect_videos_on_page(url):
    """Detect videos on any webpage"""
    try:
        log_to_console(f"Detecting videos on: {url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        videos = []
        
        # Find video elements
        for video in soup.find_all('video'):
            for source in video.find_all('source'):
                if source.get('src'):
                    video_url = source['src']
                    if not video_url.startswith('http'):
                        # Handle relative URLs
                        from urllib.parse import urljoin
                        video_url = urljoin(url, video_url)
                    videos.append({
                        'url': video_url,
                        'type': 'video_element',
                        'title': video.get('title', 'Unknown Video')
                    })
        
        # Find video URLs in page source using patterns
        video_patterns = [
            r'https?://[^\s<>"]+\.(mp4|webm|mov|avi|m4v)',
            r'https?://[^\s<>"]+video[^\s<>"]*',
            r'https?://[^\s<>"]+\.(mp4|webm|mov|avi|m4v)\?[^\s<>"]*',
        ]
        
        for pattern in video_patterns:
            matches = re.findall(pattern, response.text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    video_url = match[0] if match[0].startswith('http') else f"https://{match[0]}"
                else:
                    video_url = match if match.startswith('http') else f"https://{match}"
                
                if video_url not in [v['url'] for v in videos]:
                    videos.append({
                        'url': video_url,
                        'type': 'pattern_match',
                        'title': f'Detected Video ({video_url.split("/")[-1]})'
                    })
        
        log_to_console(f"Found {len(videos)} videos on page")
        return videos
        
    except Exception as e:
        log_to_console(f"Error detecting videos: {str(e)}")
        return []

def try_ytdlp_generic_extractor(url):
    """Try yt-dlp's generic extractor for unknown sites"""
    try:
        log_to_console(f"Trying yt-dlp generic extractor for: {url}")
        
        ydl_opts = {
            'format': 'best',
            'extract_flat': True,  # Just get info, don't download
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            if info:
                log_to_console(f"yt-dlp found video: {info.get('title', 'Unknown')}")
                return {
                    'url': info.get('url') or info.get('webpage_url'),
                    'type': 'ytdlp_generic',
                    'title': info.get('title', 'Unknown Video'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader', 'Unknown')
                }
    except Exception as e:
        log_to_console(f"yt-dlp generic extractor failed: {str(e)}")
    
    return None

def normalize_filename(title, extractor_key, uploader, is_mp3=False):
    """Normalize filename according to specifications"""
    # Strip #, emojis, and special characters
    title = re.sub(r'[#@$%^&*()_+=\[\]{}|\\:";\'<>?,./]', '', title)
    title = re.sub(r'[^\w\s.-]', '', title)  # Keep only alphanumeric, spaces, dots, hyphens
    
    # Take only the first 6 words
    words = title.split()
    title = ' '.join(words[:6]) if len(words) > 6 else title
    
    # Replace spaces with periods
    title = title.replace(' ', '.')
    
    # Get origin prefix from config
    origin = app.config['PLATFORM_NAMES'].get(extractor_key, extractor_key[:2].upper())
    
    # Clean uploader name
    uploader = re.sub(r'[^\w]', '', uploader) if uploader else 'unknown'
    
    # Ensure proper extension
    extension = '.mp3' if is_mp3 else '.mp4'
    
    # New format: ORIGIN.Just.First.Six.Words.CHANNEL.mp4
    return f"{origin}.{title}.{uploader}{extension}"

@app.route('/')
def index():
    return redirect(url_for('dl'))

@app.route('/dl')
def dl():
    return render_template("dl.html")

@app.route('/sort')
def sort():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    # Sort files by modification time (newest first)
    files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return render_template("sort.html", files=files)

@app.route('/transcribe')
def transcribe():
    downloads = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.mp3'))]
    downloads.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    transcripts = [f for f in os.listdir(app.config['SUBTITLE_FOLDER']) if f.endswith('.txt')]
    transcripts.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['SUBTITLE_FOLDER'], x)), reverse=True)
    return render_template("transcribe.html", downloads=downloads, transcripts=transcripts)

@app.route('/console')
def console():
    return render_template("console.html")

@app.route('/console/stream')
def console_stream():
    def generate():
        last_index = 0
        while True:
            if len(console_logs) > last_index:
                for i in range(last_index, len(console_logs)):
                    yield f"data: {console_logs[i]}\n\n"
                last_index = len(console_logs)
            time.sleep(0.1)
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    links = data.get('links', [])[:app.config['MAX_LINKS_PER_REQUEST']]  # Limit based on config
    mp3_only = data.get('mp3', False)
    transcribe = data.get('transcribe', False)
    results = []

    log_to_console(f"Starting download of {len(links)} links")

    for i, url in enumerate(links):
        try:
            log_to_console(f"Processing link {i+1}/{len(links)}: {url}")
            uid = str(uuid.uuid4())[:8]
            info = {'url': url, 'index': i}
            
            # Get cookies file for this URL
            cookies_file = get_cookies_file(url)
            
            # Enhanced yt-dlp options with Instagram-specific settings
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
                'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], f'{uid}.%(ext)s'),
                'quiet': False,  # Changed to False to capture output
                'no_warnings': False,  # Changed to False to capture warnings
                'user_agent': app.config['USER_AGENT'],
                'retries': 3,
                'fragment_retries': 3,
                'progress_hooks': [lambda d: log_to_console(f"Download progress: {d.get('_percent_str', '0%')} - {d.get('_speed_str', 'N/A')} - ETA: {d.get('_eta_str', 'N/A')}") if d.get('status') == 'downloading' else None],
                'logger': ConsoleLogger(),  # Use custom logger
            }
            
            # Always use cookies for Instagram
            if 'instagram' in url.lower():
                instagram_cookies = os.path.join('cookies', 'instagram_cookies.txt')
                if os.path.exists(instagram_cookies):
                    ydl_opts['cookiefile'] = instagram_cookies
                    log_to_console(f"Using Instagram cookies: {instagram_cookies}")
            # Add cookies if available for other platforms
            elif cookies_file:
                ydl_opts['cookiefile'] = cookies_file
                log_to_console(f"Using cookies file: {cookies_file}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                log_to_console(f"Extracting info for: {url}")
                meta = ydl.extract_info(url, download=False)
                title = meta.get('title', 'video')
                extractor_key = meta.get('extractor_key', 'Unknown')
                uploader = meta.get('uploader', 'unknown')
                
                # Check if file already exists
                normalized_name = normalize_filename(title, extractor_key, uploader, mp3_only)
                final_file = os.path.join(app.config['UPLOAD_FOLDER'], normalized_name)
                
                if os.path.exists(final_file):
                    log_to_console(f"File already exists: {normalized_name}")
                    results.append({
                        'url': url,
                        'index': i,
                        'filename': normalized_name,
                        'title': title,
                        'uploader': uploader,
                        'platform': extractor_key,
                        'status': 'already_exists',
                        'message': 'File already downloaded bro, check Sort'
                    })
                    continue
                
                log_to_console(f"Downloading: {title} from {extractor_key}")
                
                # Try download with current format, if it fails, try fallback formats
                download_success = False
                fallback_formats = [
                    'best[height<=1080]/bestvideo+bestaudio/best',
                    'bestvideo+bestaudio/best',
                    'best',
                    'worst'  # Last resort
                ]
                
                for format_index, fallback_format in enumerate(fallback_formats):
                    if format_index == 0:
                        # Use the configured format first
                        current_format = ydl_opts['format']
                    else:
                        # Use fallback formats
                        current_format = fallback_format
                    
                    try:
                        log_to_console(f"Trying format: {current_format}")
                        ydl.params['format'] = current_format
                        log_to_console(f"Starting download with format: {current_format}")
                        ydl.download([url])
                        
                        # Check if file was downloaded
                        downloaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(uid)]
                        if downloaded_files:
                            download_success = True
                            log_to_console(f"Download successful with format: {current_format}")
                            break
                        else:
                            log_to_console(f"Format {current_format} failed, trying next...")
                    except Exception as e:
                        log_to_console(f"Format {current_format} failed: {str(e)}, trying next...")
                        continue
                
                if not download_success:
                    raise Exception("All download formats failed")
                
                # Find the downloaded file
                downloaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(uid)]
                if not downloaded_files:
                    raise Exception("No file downloaded")
                
                temp_file = os.path.join(app.config['UPLOAD_FOLDER'], downloaded_files[0])
                
                # Rename to final name
                if os.path.exists(temp_file):
                    os.rename(temp_file, final_file)
                
                log_to_console(f"Downloaded: {normalized_name}")
                
                info['filename'] = normalized_name
                info['title'] = title
                info['uploader'] = uploader
                info['platform'] = extractor_key
                
                # Convert to MP3 if requested
                if mp3_only and not normalized_name.endswith('.mp3'):
                    audio_path = final_file.replace('.mp4', '.mp3')
                    try:
                        log_to_console(f"Converting to MP3: {normalized_name}")
                        ffmpeg.input(final_file).output(audio_path, acodec='mp3').run(overwrite_output=True, quiet=True)
                        os.remove(final_file)  # Remove video file
                        info['filename'] = os.path.basename(audio_path)
                        final_file = audio_path
                        log_to_console(f"Converted to MP3: {os.path.basename(audio_path)}")
                    except Exception as e:
                        log_to_console(f"MP3 conversion failed: {str(e)}")
                
                # Transcribe if requested
                if transcribe:
                    try:
                        log_to_console(f"Transcribing file: {final_file}")
                        result = model.transcribe(final_file)
                        text = result['text'].strip()
                        sub_file = normalized_name.replace('.mp4', '.txt').replace('.mp3', '.txt')
                        sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
                        
                        with open(sub_path, 'w', encoding='utf-8') as f:
                            f.write(text)
                        
                        info['transcript'] = sub_file
                        info['transcript_length'] = len(text)
                        log_to_console(f"Transcription complete: {sub_file} ({len(text)} chars)")
                    except Exception as e:
                        info['transcript_error'] = str(e)
                        log_to_console(f"Transcription failed: {str(e)}")
                
                results.append(info)

        except Exception as e:
            log_to_console(f"Error processing {url}: {str(e)}")
            results.append({
                'url': url, 
                'index': i, 
                'error': str(e),
                'status': 'failed'
            })

    log_to_console(f"Download session complete: {len([r for r in results if not r.get('error')])} successful, {len([r for r in results if r.get('error')])} failed")
    return jsonify(results)

@app.route('/downloads/<path:filename>')
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/subtitles/<path:filename>')
def subtitle_file(filename):
    return send_from_directory(app.config['SUBTITLE_FOLDER'], filename)

@app.route('/rename', methods=['POST'])
def rename():
    old = request.form['old']
    new = request.form['new']
    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old)
    new_path = os.path.join(app.config['UPLOAD_FOLDER'], new)
    
    if os.path.exists(old_path) and not os.path.exists(new_path):
        os.rename(old_path, new_path)
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'File not found or new name already exists'})

@app.route('/delete', methods=['POST'])
def delete():
    target = request.form['target']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], target)
    subtitle_path = os.path.join(app.config['SUBTITLE_FOLDER'], target)
    deleted = False
    if os.path.exists(file_path):
        os.remove(file_path)
        deleted = True
    if os.path.exists(subtitle_path):
        os.remove(subtitle_path)
        deleted = True
    if deleted:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'File not found'})

@app.route('/load_subtitle', methods=['POST'])
def load_subtitle():
    filename = request.form['filename']
    file_path = os.path.join(app.config['SUBTITLE_FOLDER'], filename)
    
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content, 'success': True})
    else:
        return jsonify({'success': False, 'error': 'File not found'})

@app.errorhandler(500)
def handle_500_error(e):
    return jsonify({'success': False, 'error': 'Internal server error'}), 500

@app.route('/translate', methods=['POST'])
def translate():
    text = request.form.get('text', '')
    lang = request.form.get('lang', '')
    orig_filename = request.form.get('filename', None)
    
    if not text or not lang:
        return jsonify({'success': False, 'error': 'Missing text or language'}), 400
    
    try:
        # Check if text is too long (Google Translate has limits)
        if len(text) > 5000:  # Split into chunks if too long
            log_to_console(f"Text too long ({len(text)} chars), splitting into chunks")
            chunks = [text[i:i+5000] for i in range(0, len(text), 5000)]
            translated_chunks = []
            
            for i, chunk in enumerate(chunks):
                try:
                    log_to_console(f"Translating chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
                    result = translator.translate(chunk, dest=lang)
                    
                    # Check for None result
                    if result is None:
                        log_to_console(f"Translation returned None for chunk {i+1}")
                        return jsonify({'success': False, 'error': f'Translation failed for chunk {i+1} - got None response'}), 500
                    
                    # Check if result has text attribute
                    if not hasattr(result, 'text') or result.text is None:
                        log_to_console(f"Translation result has no text for chunk {i+1}")
                        return jsonify({'success': False, 'error': f'Translation failed for chunk {i+1} - no text in result'}), 500
                    
                    translated_chunks.append(result.text)
                    
                    # Add small delay between chunks to avoid rate limiting
                    if i < len(chunks) - 1:
                        time.sleep(0.5)
                        
                except Exception as chunk_error:
                    log_to_console(f"Error translating chunk {i+1}: {str(chunk_error)}")
                    return jsonify({'success': False, 'error': f'Translation failed for chunk {i+1}: {str(chunk_error)}'}), 500
            
            translated = ' '.join(translated_chunks)
            log_to_console(f"Translation complete: {len(translated)} chars")
            
        else:
            # Single translation for shorter text
            log_to_console(f"Translating text ({len(text)} chars)")
            result = translator.translate(text, dest=lang)
            
            # Check for None result
            if result is None:
                log_to_console("Translation returned None")
                return jsonify({'success': False, 'error': 'Translation failed - got None response'}), 500
            
            # Check if result has text attribute
            if not hasattr(result, 'text') or result.text is None:
                log_to_console("Translation result has no text")
                return jsonify({'success': False, 'error': 'Translation failed - no text in result'}), 500
            
            translated = result.text
            log_to_console(f"Translation complete: {len(translated)} chars")
        
        # Save translation to Translations folder
        lang_suffix = '.' + lang.upper()
        if orig_filename:
            base = os.path.splitext(orig_filename)[0]
            save_name = f"{base}{lang_suffix}.txt"
        else:
            save_name = f"translation_{int(time.time())}{lang_suffix}.txt"
        save_path = os.path.join('Translations', save_name)
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(translated)
        log_to_console(f"Saved translation: {save_name}")
        
        return jsonify({'translated': translated, 'success': True, 'filename': save_name})
        
    except Exception as e:
        log_to_console(f"Translation error: {str(e)}")
        print('Translation error:', traceback.format_exc())
        return jsonify({'success': False, 'error': f'Translation failed: {str(e)}'}), 500

@app.route('/api/files')
def api_files():
    """API endpoint to get list of files"""
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    file_info = []
    
    for file in files:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file)
        file_info.append({
            'name': file,
            'size': os.path.getsize(file_path),
            'modified': os.path.getmtime(file_path),
            'type': 'video' if file.endswith(('.mp4', '.webm', '.mkv')) else 'audio' if file.endswith('.mp3') else 'other'
        })
    
    # Sort by modification time (newest first)
    file_info.sort(key=lambda x: x['modified'], reverse=True)
    return jsonify(file_info)

@app.route('/transcribe_file', methods=['POST'])
def transcribe_file():
    filename = request.form['filename']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    
    # Check file size before transcribing (from office version)
    if os.path.getsize(file_path) < 1024:  # less than 1KB
        log_to_console(f"Transcription failed: File is empty or too small to process: {filename}")
        return jsonify({'success': False, 'error': 'File is empty or too small to transcribe. Please check the file.'}), 400
    
    try:
        log_to_console(f"Transcribing file: {filename}")
        result = model.transcribe(file_path)
        text = result['text'].strip()
        sub_file = filename.rsplit('.', 1)[0] + '.txt'
        sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
        with open(sub_path, 'w', encoding='utf-8') as f:
            f.write(text)
        log_to_console(f"Transcription complete: {sub_file}")
        return jsonify({'success': True, 'content': text, 'transcript': sub_file})
    except Exception as e:
        log_to_console(f"Transcription failed: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/open_downloads_folder', methods=['POST'])
def open_downloads_folder():
    folder = app.config['UPLOAD_FOLDER']
    try:
        # Detect WSL2
        if 'WSL_DISTRO_NAME' in os.environ or 'microsoft-standard' in os.uname().release:
            unc_path = r'\\wsl.localhost\Ubuntu\home\rapsa\heyjenna\downloads'
            subprocess.Popen(['explorer.exe', unc_path])
        elif sys.platform.startswith('darwin'):
            subprocess.Popen(['open', folder])
        elif sys.platform.startswith('win'):
            subprocess.Popen(['explorer', folder])
        else:
            subprocess.Popen(['xdg-open', folder])
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/open_in_explorer', methods=['POST'])
def open_in_explorer():
    filename = request.form.get('filename')
    if not filename:
        return jsonify({'success': False, 'error': 'Missing filename'}), 400
    file_path = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    try:
        log_to_console(f"[Explorer] Trying to open: {file_path}")
        # Detect WSL2
        if 'WSL_DISTRO_NAME' in os.environ or 'microsoft-standard' in os.uname().release:
            unc_path = r'\\wsl.localhost\Ubuntu\home\rapsa\heyjenna\downloads'
            subprocess.Popen(['explorer.exe', unc_path])
        elif sys.platform.startswith('darwin'):
            cmd = ['open', '-R', file_path]
            subprocess.Popen(cmd)
        elif sys.platform.startswith('win'):
            cmd = ['explorer', f'/select,{file_path}']
            subprocess.Popen(cmd)
        else:
            cmd = ['xdg-open', os.path.dirname(file_path)]
            subprocess.Popen(cmd)
        return jsonify({'success': True, 'file_path': file_path})
    except Exception as e:
        log_to_console(f"[Explorer] Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e), 'file_path': file_path})

def get_file_info(filepath):
    try:
        cmd = [
            'ffprobe', '-v', 'error', '-show_entries',
            'format=duration,size:stream=codec_name,codec_type,avg_frame_rate',
            '-of', 'json', filepath
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            return {'success': False, 'error': result.stderr.strip()}
        info = json.loads(result.stdout)
        # Get extension
        extension = os.path.splitext(filepath)[1].replace('.', '').upper()
        # Get size
        size = os.path.getsize(filepath)
        # Format size
        def format_size(num):
            for unit in ['B','KB','MB','GB','TB']:
                if num < 1024.0:
                    return f"{num:.2f} {unit}"
                num /= 1024.0
            return f"{num:.2f} PB"
        # Duration
        duration = float(info['format'].get('duration', 0))
        mins = int(duration // 60)
        secs = int(duration % 60)
        duration_str = f"{mins}:{secs:02d}"
        # Codec and framerate
        codec = None
        framerate = None
        for stream in info.get('streams', []):
            if stream.get('codec_type') == 'video':
                codec = stream.get('codec_name')
                # avg_frame_rate is like '30000/1001'
                afr = stream.get('avg_frame_rate', '0/0')
                try:
                    num, den = afr.split('/')
                    if int(den) != 0:
                        framerate = round(int(num)/int(den), 2)
                except:
                    pass
                break
        return {
            'success': True,
            'codec': codec or 'Unknown',
            'extension': extension,
            'size': format_size(size),
            'duration': duration_str,
            'framerate': f"{framerate} fps" if framerate else 'Unknown'
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/api/file_info')
def api_file_info():
    filename = request.args.get('filename')
    if not filename:
        return jsonify({'success': False, 'error': 'Missing filename'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(file_path):
        return jsonify({'success': False, 'error': 'File not found'}), 404
    info = get_file_info(file_path)
    return jsonify(info)

@app.route('/convert', methods=['POST'])
def convert_file():
    try:
        # Accept form data instead of JSON
        filename = request.form.get('filename')
        format_type = request.form.get('format')
        
        if not filename or not format_type:
            return jsonify({'success': False, 'error': 'Missing filename or format'}), 400
            
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'success': False, 'error': 'File not found'}), 404
            
        # Generate output filename
        base_name = os.path.splitext(filename)[0]
        output_filename = f"{base_name}.{format_type}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)
        
        try:
            if format_type == 'mp3':
                # Convert to MP3 (audio only)
                (
                    ffmpeg.input(filepath)
                    .output(output_path, codec='libmp3lame', qscale=0, **{'ar': '44100', 'ac': '2'})
                    .run(overwrite_output=True)
                )
            elif format_type == 'mp4':
                # Convert to MP4 with compression
                (
                    ffmpeg.input(filepath)
                    .output(output_path, vcodec='libx264', crf=28, preset='medium', acodec='aac', **{'b:a': '128k'})
                    .run(overwrite_output=True)
                )
            elif format_type == 'gif':
                # Convert to GIF (low quality, small size)
                (
                    ffmpeg.input(filepath, ss=0)
                    .filter('fps', fps=10)
                    .filter('scale', -1, 240)
                    .output(output_path, loop=0, vf='split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse')
                    .run(overwrite_output=True)
                )
            elif format_type == 'mov':
                # Convert to MOV (high quality)
                (
                    ffmpeg.input(filepath)
                    .output(output_path, vcodec='prores_ks', profile=3, pix_fmt='yuv422p10le', acodec='pcm_s24le', **{'ar': '48000'})
                    .run(overwrite_output=True)
                )
            else:
                return jsonify({'success': False, 'error': 'Unsupported format'}), 400
                
            return jsonify({
                'success': True, 
                'message': f'File converted to {format_type.upper()} successfully',
                'new_filename': output_filename
            })
            
        except ffmpeg.Error as e:
            return jsonify({
                'success': False, 
                'error': f'FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Conversion failed: {str(e)}',
            'traceback': traceback.format_exc()
        }), 500

@app.route('/detect_videos', methods=['POST'])
def detect_videos():
    """Detect videos on any webpage"""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()
        
        if not url:
            return jsonify({'success': False, 'error': 'URL is required'}), 400
        
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        log_to_console(f"Starting video detection for: {url}")
        
        # Method 1: Try yt-dlp generic extractor first
        ytdlp_result = try_ytdlp_generic_extractor(url)
        if ytdlp_result:
            return jsonify({
                'success': True,
                'videos': [ytdlp_result],
                'method': 'ytdlp_generic'
            })
        
        # Method 2: Web scraping
        scraped_videos = detect_videos_on_page(url)
        if scraped_videos:
            return jsonify({
                'success': True,
                'videos': scraped_videos,
                'method': 'web_scraping'
            })
        
        # No videos found
        return jsonify({
            'success': True,
            'videos': [],
            'method': 'none',
            'message': 'No videos detected on this page'
        })
        
    except Exception as e:
        log_to_console(f"Video detection error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Video detection failed: {str(e)}'
        }), 500

@app.route('/test-spa')
def test_spa():
    """Test Single Page Application"""
    downloads = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.endswith(('.mp4', '.mp3'))]
    downloads.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    transcripts = [f for f in os.listdir(app.config['SUBTITLE_FOLDER']) if f.endswith('.txt')]
    transcripts.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['SUBTITLE_FOLDER'], x)), reverse=True)
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return render_template("test-spa.html", downloads=downloads, transcripts=transcripts, files=files)

def clean_incomplete_downloads():
    """Remove .part files and any incomplete downloads from the downloads folder."""
    folder = app.config['UPLOAD_FOLDER']
    removed = 0
    for fname in os.listdir(folder):
        if fname.endswith('.part') or fname.endswith('.tmp') or fname.startswith('yt-dlp-'):
            try:
                os.remove(os.path.join(folder, fname))
                removed += 1
                log_to_console(f"Removed incomplete file: {fname}")
            except Exception as e:
                log_to_console(f"Failed to remove {fname}: {e}")
    if removed:
        log_to_console(f"Cleanup complete: {removed} incomplete files removed.")
    else:
        log_to_console("Cleanup complete: No incomplete files found.")

# Run cleanup on startup
clean_incomplete_downloads()

if __name__ == '__main__':
    print(f"🚀 Starting Jenna The Temp on {app.config['HOST']}:{app.config['PORT']}")
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
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

app = Flask(__name__, static_folder='static')

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)
os.makedirs('static/SVG', exist_ok=True)

# Initialize Whisper model
print(f"Loading Whisper model: {app.config['WHISPER_MODEL']}")
model = whisper.load_model(app.config['WHISPER_MODEL'])
translator = Translator()

# Get cookie files from config
COOKIE_FILES = app.config['COOKIE_FILES']

# Console log storage
console_logs = []

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

def normalize_filename(title, extractor_key, uploader, is_mp3=False):
    """Normalize filename according to specifications"""
    # Strip #, emojis, and special characters
    title = re.sub(r'[#@$%^&*()_+=\[\]{}|\\:";\'<>?,./]', '', title)
    title = re.sub(r'[^\w\s.-]', '', title)  # Keep only alphanumeric, spaces, dots, hyphens
    
    # Replace spaces with periods
    title = title.replace(' ', '.')
    
    # Get origin prefix from config
    origin = app.config['PLATFORM_NAMES'].get(extractor_key, extractor_key[:2].upper())
    
    # Clean uploader name
    uploader = re.sub(r'[^\w]', '', uploader) if uploader else 'unknown'
    
    # Ensure proper extension
    extension = '.mp3' if is_mp3 else '.mp4'
    
    return f"{origin}-{title}.{uploader}{extension}"

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
            
            # Enhanced yt-dlp options using config
            format_string = app.config['VIDEO_QUALITY'] if not mp3_only else app.config['AUDIO_QUALITY']
            ydl_opts = {
                'format': format_string,
                'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], f'{uid}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'user_agent': app.config['USER_AGENT'],
                'retries': 3,
                'fragment_retries': 3,
                'skip_unavailable_fragments': True,
            }
            
            # Add cookies if available
            if cookies_file:
                ydl_opts['cookiefile'] = cookies_file
                log_to_console(f"Using cookies file: {cookies_file}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                log_to_console(f"Extracting info for: {url}")
                meta = ydl.extract_info(url, download=False)
                title = meta.get('title', 'video')
                extractor_key = meta.get('extractor_key', 'Unknown')
                uploader = meta.get('uploader', 'unknown')
                
                log_to_console(f"Downloading: {title} from {extractor_key}")
                # Download the file with fallback if format is unavailable
                try:
                    ydl.download([url])
                except yt_dlp.utils.DownloadError as e:
                    if 'requested format' in str(e).lower() and 'available' in str(e).lower():
                        log_to_console("Format not available, retrying with 'best'")
                        retry_opts = ydl_opts.copy()
                        retry_opts['format'] = 'best'
                        with yt_dlp.YoutubeDL(retry_opts) as retry_ydl:
                            retry_ydl.download([url])
                    else:
                        raise
                
                # Find the downloaded file
                downloaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(uid)]
                if not downloaded_files:
                    raise Exception("No file downloaded")
                
                temp_file = os.path.join(app.config['UPLOAD_FOLDER'], downloaded_files[0])
                
                # Normalize filename with correct extension
                normalized_name = normalize_filename(title, extractor_key, uploader, mp3_only)
                final_file = os.path.join(app.config['UPLOAD_FOLDER'], normalized_name)
                
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
                        log_to_console(f"Transcribing: {normalized_name}")
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
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)

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
    
    if os.path.exists(file_path):
        os.remove(file_path)
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

@app.route('/translate', methods=['POST'])
def translate():
    text = request.form['text']
    lang = request.form['lang']
    
    try:
        translated = translator.translate(text, dest=lang).text
        return jsonify({'translated': translated, 'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

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

if __name__ == '__main__':
    print(f"🚀 Starting Jenna The Temp on {app.config['HOST']}:{app.config['PORT']}")
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
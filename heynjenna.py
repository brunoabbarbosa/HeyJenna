from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
import os
import uuid
import whisper
import ffmpeg
from werkzeug.utils import secure_filename
from googletrans import Translator
import yt_dlp
import re
from config import get_config

app = Flask(__name__)

# Load configuration
config_class = get_config()
app.config.from_object(config_class)

# Create directories
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)

# Initialize Whisper model
print(f"Loading Whisper model: {app.config['WHISPER_MODEL']}")
model = whisper.load_model(app.config['WHISPER_MODEL'])
translator = Translator()

# Get cookie files from config
COOKIE_FILES = app.config['COOKIE_FILES']

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
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return render_template("index.html", files=files)

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

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    url = data.get('url', '').strip()
    
    if not url:
        return jsonify({'error': 'No URL provided'})
    
    try:
        uid = str(uuid.uuid4())[:8]
        
        # Get cookies file for this URL
        cookies_file = get_cookies_file(url)
        
        # Enhanced yt-dlp options using config
        ydl_opts = {
            'format': app.config['VIDEO_QUALITY'],
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
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Extract info first
            meta = ydl.extract_info(url, download=False)
            title = meta.get('title', 'video')
            extractor_key = meta.get('extractor_key', 'Unknown')
            uploader = meta.get('uploader', 'unknown')
            
            # Download the file
            ydl.download([url])
            
            # Find the downloaded file
            downloaded_files = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if f.startswith(uid)]
            if not downloaded_files:
                raise Exception("No file downloaded")
            
            temp_file = os.path.join(app.config['UPLOAD_FOLDER'], downloaded_files[0])
            
            # Normalize filename
            normalized_name = normalize_filename(title, extractor_key, uploader)
            final_file = os.path.join(app.config['UPLOAD_FOLDER'], normalized_name)
            
            # Rename to final name
            if os.path.exists(temp_file):
                os.rename(temp_file, final_file)
            
            return jsonify({
                'success': True,
                'title': title,
                'filename': normalized_name,
                'uploader': uploader,
                'platform': extractor_key
            })

    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    links = data.get('links', [])[:app.config['MAX_LINKS_PER_REQUEST']]  # Limit based on config
    mp3_only = data.get('mp3', False)
    transcribe = data.get('transcribe', False)
    results = []

    for i, url in enumerate(links):
        try:
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
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract info first
                meta = ydl.extract_info(url, download=False)
                title = meta.get('title', 'video')
                extractor_key = meta.get('extractor_key', 'Unknown')
                uploader = meta.get('uploader', 'unknown')
                
                # Download the file
                ydl.download([url])
                
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
                
                info['filename'] = normalized_name
                info['title'] = title
                info['uploader'] = uploader
                info['platform'] = extractor_key
                
                # Convert to MP3 if requested
                if mp3_only and not normalized_name.endswith('.mp3'):
                    audio_path = final_file.replace('.mp4', '.mp3')
                    try:
                        ffmpeg.input(final_file).output(audio_path, acodec='mp3').run(overwrite_output=True, quiet=True)
                        os.remove(final_file)  # Remove video file
                        info['filename'] = os.path.basename(audio_path)
                        final_file = audio_path
                    except Exception as e:
                        pass
                
                # Transcribe if requested
                if transcribe:
                    try:
                        result = model.transcribe(final_file)
                        text = result['text'].strip()
                        sub_file = normalized_name.replace('.mp4', '.txt').replace('.mp3', '.txt')
                        sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
                        
                        with open(sub_path, 'w', encoding='utf-8') as f:
                            f.write(text)
                        
                        info['transcript'] = sub_file
                        info['transcript_length'] = len(text)
                    except Exception as e:
                        info['transcript_error'] = str(e)
                
                results.append(info)

        except Exception as e:
            results.append({
                'url': url, 
                'index': i, 
                'error': str(e),
                'status': 'failed'
            })

    return jsonify(results)

@app.route('/file/<path:filename>')
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
    return jsonify({'success': False})

@app.route('/delete', methods=['POST'])
def delete():
    filename = request.form['filename']
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    if os.path.exists(file_path):
        os.remove(file_path)
        return jsonify({'success': True})
    return jsonify({'success': False})

@app.route('/load_subtitle', methods=['POST'])
def load_subtitle():
    filename = request.form['filename']
    sub_file = filename.replace('.mp4', '.txt').replace('.mp3', '.txt')
    sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
    
    if os.path.exists(sub_path):
        with open(sub_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return jsonify({'content': content})
    return jsonify({'content': ''})

@app.route('/translate', methods=['POST'])
def translate():
    text = request.form['text']
    src_lang = request.form.get('src_lang', 'auto')
    target_lang = request.form.get('target_lang', 'en')
    
    try:
        result = translator.translate(text, src=src_lang, dest=target_lang)
        return jsonify({'translated': result.text})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/files')
def api_files():
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    files.sort(key=lambda x: os.path.getmtime(os.path.join(app.config['UPLOAD_FOLDER'], x)), reverse=True)
    return jsonify(files)

@app.route('/edit', methods=['POST'])
def edit():
    if 'file' not in request.files:
        return 'No file uploaded', 400
    
    file = request.files['file']
    if file.filename == '':
        return 'No file selected', 400
    
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        src_lang = request.form.get('src_lang', 'auto')
        target_lang = request.form.get('target_lang', '')
        
        try:
            result = model.transcribe(filepath)
            text = result['text'].strip()
            
            if target_lang and target_lang != src_lang:
                try:
                    translated = translator.translate(text, src=src_lang, dest=target_lang)
                    translated_text = translated.text
                    
                    # Save translated transcript
                    translated_filename = filename.replace('.mp4', '_translated.txt').replace('.mp3', '_translated.txt')
                    translated_path = os.path.join(app.config['SUBTITLE_FOLDER'], translated_filename)
                    with open(translated_path, 'w', encoding='utf-8') as f:
                        f.write(translated_text)
                except Exception as e:
                    translated_text = f"Translation error: {str(e)}"
            else:
                translated_text = None
            
            return render_template('transcribe.html', transcription=text, filename=filename, translated=translated_text)
            
        except Exception as e:
            return f'Error transcribing file: {str(e)}', 500

@app.route('/save_transcript', methods=['POST'])
def save_transcript():
    text = request.form['text']
    filename = request.form['filename']
    
    sub_file = filename.replace('.mp4', '.txt').replace('.mp3', '.txt')
    sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
    
    with open(sub_path, 'w', encoding='utf-8') as f:
        f.write(text)
    
    return redirect(url_for('transcribe'))

@app.route('/console')
def console():
    return render_template('console.html')

@app.route('/console/stream')
def console_stream():
    def generate():
        # This is a placeholder for console streaming
        # In a real implementation, you'd stream actual console output
        yield "data: Console output would appear here\n\n"
    
    return app.response_class(generate(), mimetype='text/plain')

if __name__ == '__main__':
    print(f"🚀 Starting Jenna The Temp on {app.config['HOST']}:{app.config['PORT']}")
    app.run(host=app.config['HOST'], port=app.config['PORT'], debug=app.config['DEBUG'])
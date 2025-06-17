from flask import Flask, request, render_template, send_from_directory, redirect, url_for, jsonify
import os
import uuid
import whisper
import ffmpeg
from werkzeug.utils import secure_filename
from googletrans import Translator
import yt_dlp
import re

app = Flask(__name__)

# Config
app.config['UPLOAD_FOLDER'] = 'downloads'
app.config['SUBTITLE_FOLDER'] = 'subtitles'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['SUBTITLE_FOLDER'], exist_ok=True)

model = whisper.load_model("base")
translator = Translator()

# Cookie files mapping
COOKIE_FILES = {
    'tiktok.com': 'www.tiktok.com_cookies.txt',
    'youtube.com': 'www.youtube.com_cookies.txt',
    'youtu.be': 'www.youtube.com_cookies.txt',
    'instagram.com': 'www.instagram.com_cookies.txt',
    'fb.watch': 'www.facebook.com_cookies.txt'
}

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
    
    # Get origin prefix
    origin_map = {
        'Youtube': 'YT',
        'TikTok': 'TT', 
        'Instagram': 'IG',
        'Facebook': 'FB',
        'Twitter': 'TW'
    }
    origin = origin_map.get(extractor_key, extractor_key[:2].upper())
    
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

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    links = data.get('links', [])[:10]  # Limit to 10 links
    mp3_only = data.get('mp3', False)
    transcribe = data.get('transcribe', False)
    results = []

    for i, url in enumerate(links):
        try:
            uid = str(uuid.uuid4())[:8]
            info = {'url': url, 'index': i}
            
            # Get cookies file for this URL
            cookies_file = get_cookies_file(url)
            
            # Enhanced yt-dlp options
            ydl_opts = {
                'format': 'bestvideo[ext=mp4][height<=1080]+bestaudio[ext=m4a]/best[ext=mp4]/best' if not mp3_only else 'bestaudio[ext=m4a]/bestaudio/best',
                'outtmpl': os.path.join(app.config['UPLOAD_FOLDER'], f'{uid}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
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
        result = model.transcribe(file_path)
        text = result['text'].strip()
        sub_file = filename.rsplit('.', 1)[0] + '.txt'
        sub_path = os.path.join(app.config['SUBTITLE_FOLDER'], sub_file)
        with open(sub_path, 'w', encoding='utf-8') as f:
            f.write(text)
        return jsonify({'success': True, 'content': text, 'transcript': sub_file})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5000)
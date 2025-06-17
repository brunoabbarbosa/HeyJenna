"""
Configuration file for Jeff The Temp - Multi-Platform Video Downloader
"""

import os

class Config:
    """Base configuration"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jeff-the-temp-secret-key-change-in-production'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    HOST = os.environ.get('FLASK_HOST', '0.0.0.0')
    PORT = int(os.environ.get('FLASK_PORT', 5000))
    
    # Directory settings
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'downloads')
    SUBTITLE_FOLDER = os.environ.get('SUBTITLE_FOLDER', 'subtitles')
    
    # Download settings
    MAX_LINKS_PER_REQUEST = int(os.environ.get('MAX_LINKS_PER_REQUEST', 10))
    MAX_FILE_SIZE_MB = int(os.environ.get('MAX_FILE_SIZE_MB', 500))
    
    # Whisper model settings
    WHISPER_MODEL = os.environ.get('WHISPER_MODEL', 'base')
    # Available models: tiny, base, small, medium, large
    # Larger models are more accurate but slower and use more memory
    
    # Video quality settings
    VIDEO_QUALITY = os.environ.get('VIDEO_QUALITY', 'best[height<=1080]')
    AUDIO_QUALITY = os.environ.get('AUDIO_QUALITY', 'bestaudio')
    
    # Cookie files mapping
    COOKIE_FILES = {
        'tiktok.com': 'www.tiktok.com_cookies.txt',
        'youtube.com': 'www.youtube.com_cookies.txt',
        'youtu.be': 'www.youtube.com_cookies.txt',
        'instagram.com': 'www.instagram.com_cookies.txt',
        'fb.watch': 'www.facebook.com_cookies.txt'
    }
    
    # User agent for downloads
    USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    
    # Supported platforms
    SUPPORTED_PLATFORMS = [
        'tiktok.com',
        'youtube.com', 
        'youtu.be',
        'instagram.com',
        'fb.watch'
    ]
    
    # Platform name mapping
    PLATFORM_NAMES = {
        'Youtube': 'YT',
        'TikTok': 'TT', 
        'Instagram': 'IG',
        'Facebook': 'FB',
        'Twitter': 'TW'
    }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    # In production, you might want to use a proper secret key
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'change-this-in-production'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])
@echo off
echo Starting HeyJenna...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.10+ from https://python.org
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist "env\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv env
    if errorlevel 1 (
        echo Error: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call env\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install requirements
    pause
    exit /b 1
)

REM Check if FFmpeg is installed
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo Warning: FFmpeg not found in PATH
    echo Please install FFmpeg from https://ffmpeg.org/download.html
    echo Add FFmpeg to your system PATH
    echo.
    echo Press any key to continue anyway...
    pause >nul
)

REM Run the application
echo Starting HeyJenna server...
echo Access the web interface at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.
python heyjenna.py

pause 
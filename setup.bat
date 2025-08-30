@echo off
REM Audio Whisper Setup Script for Windows
REM This script sets up the complete environment for audio transcription

echo ========================================
echo Audio Whisper Transcription Setup
echo ========================================
echo.

REM Check Python installation
echo Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH.
    echo Please install Python 3.8 or higher from:
    echo   https://www.python.org/downloads/
    echo.
    echo Make sure to check "Add Python to PATH" during installation!
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found
echo.

REM Check FFmpeg installation
echo Checking FFmpeg installation...
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo Warning: FFmpeg is not installed. It's required for audio processing.
    echo.
    echo To install FFmpeg:
    echo   1. Download from: https://ffmpeg.org/download.html
    echo   2. Extract to C:\ffmpeg
    echo   3. Add C:\ffmpeg\bin to your PATH
    echo.
    set /p CONTINUE="Continue without FFmpeg? (y/n): "
    if /i not "%CONTINUE%"=="y" exit /b 1
) else (
    echo FFmpeg found
)
echo.

REM Create virtual environment
echo Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping creation.
) else (
    python -m venv venv
    echo Virtual environment created
)
echo.

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Install dependencies
echo Installing dependencies...
python -m pip install --quiet --upgrade pip
pip install --quiet flask openai yt-dlp pydub
echo Dependencies installed
echo.

REM Check for OpenAI API key
echo Checking OpenAI API key...
if "%OPENAI_API_KEY%"=="" (
    echo Warning: OPENAI_API_KEY is not set
    echo.
    echo You need an OpenAI API key to use this application.
    echo Get one at: https://platform.openai.com/api-keys
    echo.
    set /p API_KEY="Enter your OpenAI API key (or press Enter to skip): "
    
    if not "!API_KEY!"=="" (
        setx OPENAI_API_KEY "!API_KEY!" >nul 2>&1
        set OPENAI_API_KEY=!API_KEY!
        echo.
        echo API key saved to environment variables
        echo You may need to restart your terminal for it to take effect
    ) else (
        echo.
        echo Remember to set OPENAI_API_KEY before running the app:
        echo   set OPENAI_API_KEY=your-key-here
    )
) else (
    echo OpenAI API key found
)
echo.

REM Create data directories
echo Creating data directories...
if not exist data mkdir data
if not exist data\audio mkdir data\audio
if not exist data\transcripts mkdir data\transcripts
if not exist data\subtitles mkdir data\subtitles
echo Directories created
echo.

REM Create run script
echo Creating run script...
(
echo @echo off
echo call venv\Scripts\activate.bat
echo python app.py
echo pause
) > run.bat
echo Run script created
echo.

echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo To start the application:
echo   run.bat
echo.
echo Or manually:
echo   venv\Scripts\activate.bat
echo   python app.py
echo.
echo Then open your browser to: http://localhost:5000
echo.

set /p START_NOW="Start the application now? (y/n): "
if /i "%START_NOW%"=="y" (
    echo Starting application...
    python app.py
)

pause
# YouTube Whisper Transcription

Minimalist YouTube video transcription using OpenAI's Whisper API.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (required for audio processing):
- **Ubuntu/Debian**: `sudo apt-get install ffmpeg`
- **macOS**: `brew install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. Set OpenAI API key:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

## Usage

1. Start the application:
```bash
python app.py
```

2. Open browser to `http://localhost:5000`

3. Enter YouTube URL and click "Process Video"

## Features

- Downloads YouTube videos as audio
- Transcribes using OpenAI Whisper API
- Handles large files by splitting into chunks
- Generates JSON (with timestamps), plain text, and SRT subtitle files
- Support for multiple languages
- Cookie support for private videos

## Directory Structure

```
data/
├── audio/        # Downloaded MP3 files
├── transcripts/  # JSON and TXT transcriptions
└── subtitles/    # SRT subtitle files
```

## Configuration

Environment variables:
- `OPENAI_API_KEY`: Required for Whisper API
- `KEEP_AUDIO_FILES`: Set to "true" to keep downloaded audio files

## Private Videos

For private or age-restricted videos:
1. Export cookies from browser using a cookies extension
2. Paste the cookies.txt content into the Cookies field
3. Process normally

## Limitations

- Maximum file size for Whisper API: 25MB (automatically handled by splitting)
- Supported audio formats: MP3, WAV, M4A, FLAC, OGG
- Requires active internet connection for YouTube downloads and API calls
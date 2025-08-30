"""Audio Transcription Application using OpenAI's Whisper API.

Standalone application for transcribing audio files and YouTube videos.
Follows minimalist programming principles with maximum signal-to-noise ratio.
"""

import os
import json
import logging
import re
import math
from datetime import datetime
from pathlib import Path

from flask import Flask, render_template_string, request, jsonify, send_file
import yt_dlp
from openai import OpenAI
from pydub import AudioSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")

DATA_DIR = Path("data")
AUDIO_DIR = DATA_DIR / "audio"
TRANSCRIPT_DIR = DATA_DIR / "transcripts"
SUBTITLE_DIR = DATA_DIR / "subtitles"
MAX_FILE_SIZE_MB = 24

# Create directories
for directory in [AUDIO_DIR, TRANSCRIPT_DIR, SUBTITLE_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)

# HTML Template (embedded for simplicity)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Audio Transcription - Whisper</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.5;
            color: #111827;
            background: #f3f4f6;
            padding: 24px;
        }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { font-size: 32px; font-weight: 600; margin-bottom: 32px; }
        .card { background: #ffffff; border: 1px solid #e5e7eb; padding: 24px; margin-bottom: 24px; }
        label { display: block; font-size: 14px; font-weight: 600; margin-bottom: 8px; color: #6b7280; }
        input[type="text"], select, textarea { 
            width: 100%; 
            padding: 8px 12px; 
            border: 1px solid #e5e7eb; 
            font-size: 16px;
            margin-bottom: 16px;
        }
        textarea { height: 96px; font-family: monospace; font-size: 14px; }
        button { 
            background: #64748b; 
            color: white; 
            padding: 8px 24px; 
            border: none; 
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
        }
        button:hover { background: #475569; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        .checkbox-container { display: flex; align-items: center; margin-bottom: 16px; }
        .checkbox-container input { width: auto; margin-right: 8px; margin-bottom: 0; }
        #results { display: none; }
        .info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 16px; }
        .info-box { background: #f3f4f6; padding: 16px; }
        .info-box h3 { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
        .info-box p { font-size: 14px; margin-bottom: 4px; }
        .download-links a { 
            display: block; 
            padding: 8px 12px; 
            background: #f3f4f6; 
            color: #111827;
            text-decoration: none;
            margin-bottom: 8px;
            font-size: 14px;
        }
        .download-links a:hover { background: #e5e7eb; }
        #log { 
            background: #f3f4f6; 
            padding: 16px; 
            height: 200px; 
            overflow-y: auto; 
            font-family: monospace;
            font-size: 12px;
            border: 1px solid #e5e7eb;
        }
        .log-entry { padding: 2px 0; }
        .error { color: #dc2626; }
        #transcript-preview { 
            background: #f3f4f6; 
            padding: 16px; 
            max-height: 240px; 
            overflow-y: auto;
            font-size: 14px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Audio Transcription</h1>
        
        <div class="card">
            <label>Input Source</label>
            <select id="input-source" onchange="toggleInputMethod()">
                <option value="file">Audio File</option>
                <option value="youtube">YouTube URL</option>
            </select>
            
            <div id="file-input-section">
                <label>Select Audio File</label>
                <input type="file" id="audio-file" accept=".mp3,.wav,.m4a,.flac,.ogg,audio/*">
            </div>
            
            <div id="youtube-input-section" style="display: none;">
                <label>YouTube URL</label>
                <input type="text" id="youtube-url" placeholder="https://www.youtube.com/watch?v=...">
                
                <label>Cookies (for private videos)</label>
                <textarea id="cookies" placeholder="Paste youtube_cookies.txt content here"></textarea>
                
                <div class="checkbox-container">
                    <input type="checkbox" id="force-download">
                    <label for="force-download">Force re-download</label>
                </div>
            </div>
            
            <label>Language</label>
            <select id="language">
                <option value="en">English</option>
                <option value="es">Spanish</option>
                <option value="fr">French</option>
                <option value="de">German</option>
                <option value="it">Italian</option>
                <option value="pt">Portuguese</option>
                <option value="ja">Japanese</option>
                <option value="zh">Chinese</option>
            </select>
            
            <button id="process-btn" onclick="process()">Process</button>
        </div>
        
        <div id="results" class="card">
            <h2 style="font-size: 20px; font-weight: 600; margin-bottom: 16px;">Results</h2>
            
            <div class="info-grid">
                <div class="info-box">
                    <h3>Video Information</h3>
                    <p>ID: <span id="video-id"></span></p>
                    <p>Time: <span id="processing-time"></span>s</p>
                    <p>Segments: <span id="segment-count"></span></p>
                </div>
                
                <div class="info-box download-links">
                    <h3>Download Files</h3>
                    <a id="json-link" href="#">JSON (with timestamps)</a>
                    <a id="txt-link" href="#">Plain Text</a>
                    <a id="srt-link" href="#">SRT Subtitles</a>
                </div>
            </div>
            
            <label>Transcript Preview</label>
            <div id="transcript-preview"></div>
        </div>
        
        <div class="card">
            <label>Processing Log</label>
            <div id="log"></div>
        </div>
    </div>
    
    <script>
        function toggleInputMethod() {
            const source = document.getElementById('input-source').value;
            document.getElementById('file-input-section').style.display = source === 'file' ? 'block' : 'none';
            document.getElementById('youtube-input-section').style.display = source === 'youtube' ? 'block' : 'none';
        }
        
        function log(message, isError = false) {
            const logDiv = document.getElementById('log');
            const entry = document.createElement('div');
            entry.className = isError ? 'log-entry error' : 'log-entry';
            const time = new Date().toLocaleTimeString();
            entry.textContent = `[${time}] ${message}`;
            logDiv.appendChild(entry);
            logDiv.scrollTop = logDiv.scrollHeight;
        }
        
        async function process() {
            const source = document.getElementById('input-source').value;
            
            if (source === 'youtube') {
                await processYouTube();
            } else {
                await processFile();
            }
        }
        
        async function processFile() {
            const fileInput = document.getElementById('audio-file');
            const language = document.getElementById('language').value;
            
            if (!fileInput.files || fileInput.files.length === 0) {
                log('Please select an audio file', true);
                return;
            }
            
            const file = fileInput.files[0];
            const button = document.getElementById('process-btn');
            button.disabled = true;
            button.textContent = 'Processing...';
            
            document.getElementById('results').style.display = 'none';
            
            log(`Processing file: ${file.name}`);
            
            const formData = new FormData();
            formData.append('audio_file', file);
            formData.append('language', language);
            
            try {
                const response = await fetch('/transcribe-file', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (data.error) {
                    log(data.error, true);
                } else {
                    log('Transcription successful');
                    displayResults(data);
                }
            } catch (error) {
                log(`Error: ${error.message}`, true);
            } finally {
                button.disabled = false;
                button.textContent = 'Process';
            }
        }
        
        async function processYouTube() {
            const url = document.getElementById('youtube-url').value.trim();
            const language = document.getElementById('language').value;
            const cookies = document.getElementById('cookies').value.trim();
            const forceDownload = document.getElementById('force-download').checked;
            
            if (!url) {
                log('Please enter a YouTube URL', true);
                return;
            }
            
            const button = document.getElementById('process-btn');
            button.disabled = true;
            button.textContent = 'Processing...';
            
            document.getElementById('results').style.display = 'none';
            
            log('Starting YouTube processing...');
            
            try {
                const response = await fetch('/transcribe-youtube', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        youtube_url: url,
                        language: language,
                        cookies_text: cookies,
                        force_download: forceDownload
                    })
                });
                
                const data = await response.json();
                
                if (data.error) {
                    log(data.error, true);
                } else {
                    log('Transcription successful');
                    displayResults(data);
                }
            } catch (error) {
                log(`Error: ${error.message}`, true);
            } finally {
                button.disabled = false;
                button.textContent = 'Process';
            }
        }
        
        function displayResults(data) {
            document.getElementById('video-id').textContent = data.file_id || data.video_id;
            document.getElementById('processing-time').textContent = data.processing_time.toFixed(2);
            document.getElementById('segment-count').textContent = data.segment_count;
            document.getElementById('transcript-preview').textContent = data.text_excerpt;
            
            const fileId = data.file_id || data.video_id;
            document.getElementById('json-link').href = `/download/${fileId}/json`;
            document.getElementById('txt-link').href = `/download/${fileId}/txt`;
            document.getElementById('srt-link').href = `/download/${fileId}/srt`;
            
            document.getElementById('results').style.display = 'block';
        }
        
        // Clear log on load
        log('Ready to process audio files or YouTube videos');
    </script>
</body>
</html>
"""

def extract_video_id(youtube_url):
    """Extract video ID from YouTube URL."""
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([^&\n?#]+)',
        r'youtube\.com\/embed\/([^&\n?#]+)',
        r'youtube\.com\/v\/([^&\n?#]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, youtube_url)
        if match:
            return match.group(1)
    return None

def download_audio(video_id, force_download=False):
    """Download audio from YouTube video."""
    output_file = AUDIO_DIR / f"{video_id}.mp3"
    
    if output_file.exists() and not force_download:
        logger.info(f"Audio already exists: {output_file}")
        return str(output_file)
    
    video_url = f"https://www.youtube.com/watch?v={video_id}"
    logger.info(f"Downloading: {video_url}")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': str(AUDIO_DIR / f"{video_id}.%(ext)s"),
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    
    if output_file.exists():
        logger.info(f"Downloaded: {output_file}")
        return str(output_file)
    return None

def split_audio(audio_file, chunk_duration_seconds=600):
    """Split large audio file into chunks."""
    audio = AudioSegment.from_file(audio_file)
    total_duration = len(audio) / 1000
    num_chunks = math.ceil(total_duration / chunk_duration_seconds)
    
    logger.info(f"Splitting into {num_chunks} chunks")
    
    chunk_files = []
    for i in range(num_chunks):
        start_ms = i * chunk_duration_seconds * 1000
        end_ms = min((i + 1) * chunk_duration_seconds * 1000, len(audio))
        
        chunk = audio[start_ms:end_ms]
        chunk_file = audio_file.replace('.mp3', f'_chunk_{i+1}.mp3')
        chunk.export(chunk_file, format="mp3")
        chunk_files.append(chunk_file)
        
    return chunk_files

def transcribe_audio(audio_file, language="en"):
    """Transcribe audio using Whisper API."""
    file_size_mb = os.path.getsize(audio_file) / (1024 * 1024)
    logger.info(f"Transcribing {audio_file} ({file_size_mb:.2f} MB)")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Handle large files
    if file_size_mb > MAX_FILE_SIZE_MB:
        logger.info("File too large, splitting...")
        chunk_files = split_audio(audio_file)
        
        transcripts = []
        for chunk_file in chunk_files:
            with open(chunk_file, "rb") as audio:
                response = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio,
                    language=language,
                    response_format="verbose_json",
                    timestamp_granularities=["segment"]
                )
            
            transcripts.append({
                "text": response.text,
                "segments": [dict(s) for s in response.segments] if hasattr(response, 'segments') else []
            })
            
            # Clean up chunk
            os.remove(chunk_file)
        
        # Merge transcripts
        return merge_transcripts(transcripts)
    else:
        with open(audio_file, "rb") as audio:
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"]
            )
        
        return {
            "text": response.text,
            "segments": [dict(s) for s in response.segments] if hasattr(response, 'segments') else []
        }

def merge_transcripts(chunks):
    """Merge multiple transcript chunks."""
    full_text = []
    all_segments = []
    time_offset = 0
    
    for chunk in chunks:
        full_text.append(chunk.get("text", ""))
        
        for segment in chunk.get("segments", []):
            if "start" in segment:
                segment["start"] += time_offset
            if "end" in segment:
                segment["end"] += time_offset
            all_segments.append(segment)
        
        if chunk.get("segments") and "end" in chunk["segments"][-1]:
            time_offset = chunk["segments"][-1]["end"]
    
    return {
        "text": " ".join(full_text),
        "segments": all_segments
    }

def save_transcript(video_id, transcript):
    """Save transcript as JSON and text files."""
    # Save JSON
    json_file = TRANSCRIPT_DIR / f"{video_id}.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "video_id": video_id,
            "text": transcript["text"],
            "segments": transcript["segments"],
            "processed_at": datetime.now().isoformat()
        }, f, ensure_ascii=False, indent=2)
    
    # Save plain text
    txt_file = TRANSCRIPT_DIR / f"{video_id}.txt"
    with open(txt_file, 'w', encoding='utf-8') as f:
        f.write(transcript["text"])
    
    return str(json_file)

def generate_srt(video_id, transcript):
    """Generate SRT subtitle file."""
    srt_file = SUBTITLE_DIR / f"{video_id}.srt"
    
    with open(srt_file, 'w', encoding='utf-8') as f:
        for i, segment in enumerate(transcript.get("segments", [])):
            # SRT index
            f.write(f"{i+1}\n")
            
            # Timestamps
            start = format_srt_time(segment.get("start", 0))
            end = format_srt_time(segment.get("end", 0))
            f.write(f"{start} --> {end}\n")
            
            # Text
            f.write(f"{segment.get('text', '').strip()}\n\n")
    
    return str(srt_file)

def format_srt_time(seconds):
    """Format seconds as SRT timestamp."""
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = seconds % 60
    millis = int((secs - int(secs)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(secs):02d},{millis:03d}"

@app.route('/')
def index():
    """Main interface."""
    return render_template_string(HTML_TEMPLATE)

@app.route('/transcribe-file', methods=['POST'])
def transcribe_file():
    """Process uploaded audio file transcription."""
    try:
        if 'audio_file' not in request.files:
            return jsonify({'error': 'No audio file uploaded'}), 400
        
        audio_file = request.files['audio_file']
        language = request.form.get('language', 'en')
        
        if audio_file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Generate unique file ID
        from uuid import uuid4
        file_id = f"upload_{uuid4().hex[:10]}"
        
        # Save uploaded file
        file_ext = audio_file.filename.rsplit('.', 1)[1].lower() if '.' in audio_file.filename else 'mp3'
        temp_file = AUDIO_DIR / f"{file_id}.{file_ext}"
        audio_file.save(str(temp_file))
        
        start_time = datetime.now()
        
        # Transcribe
        transcript = transcribe_audio(str(temp_file), language)
        if not transcript:
            return jsonify({'error': 'Failed to transcribe audio'}), 500
        
        # Save files
        save_transcript(file_id, transcript)
        generate_srt(file_id, transcript)
        
        # Clean up audio
        if not os.environ.get("KEEP_AUDIO_FILES"):
            os.remove(temp_file)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return jsonify({
            'file_id': file_id,
            'processing_time': processing_time,
            'segment_count': len(transcript.get("segments", [])),
            'character_count': len(transcript.get("text", "")),
            'text_excerpt': transcript["text"][:500] + "..." if len(transcript["text"]) > 500 else transcript["text"]
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transcribe-youtube', methods=['POST'])
def transcribe_youtube():
    """Process YouTube video transcription."""
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url')
        language = data.get('language', 'en')
        force_download = data.get('force_download', False)
        
        if not youtube_url:
            return jsonify({'error': 'YouTube URL required'}), 400
        
        # Extract video ID
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400
        
        start_time = datetime.now()
        
        # Download audio
        audio_file = download_audio(video_id, force_download)
        if not audio_file:
            return jsonify({'error': 'Failed to download audio'}), 500
        
        # Transcribe
        transcript = transcribe_audio(audio_file, language)
        if not transcript:
            return jsonify({'error': 'Failed to transcribe audio'}), 500
        
        # Save files
        save_transcript(video_id, transcript)
        generate_srt(video_id, transcript)
        
        # Clean up audio
        if not os.environ.get("KEEP_AUDIO_FILES"):
            os.remove(audio_file)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        return jsonify({
            'video_id': video_id,
            'processing_time': processing_time,
            'segment_count': len(transcript.get("segments", [])),
            'character_count': len(transcript.get("text", "")),
            'text_excerpt': transcript["text"][:500] + "..." if len(transcript["text"]) > 500 else transcript["text"]
        })
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/download/<file_id>/<file_type>')
def download(file_id, file_type):
    """Download transcript files."""
    if file_type == 'json':
        file_path = TRANSCRIPT_DIR / f"{file_id}.json"
        mime_type = 'application/json'
    elif file_type == 'txt':
        file_path = TRANSCRIPT_DIR / f"{file_id}.txt"
        mime_type = 'text/plain'
    elif file_type == 'srt':
        file_path = SUBTITLE_DIR / f"{file_id}.srt"
        mime_type = 'application/x-subrip'
    else:
        return jsonify({'error': 'Invalid file type'}), 400
    
    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404
    
    return send_file(
        file_path,
        mimetype=mime_type,
        as_attachment=True,
        download_name=f"{file_id}.{file_type}"
    )

if __name__ == '__main__':
    app.run(debug=False, port=5000)
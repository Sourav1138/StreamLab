import os
import sys
import json
import shutil
import subprocess
import threading
import time
import re
import queue
import glob
import uuid
import logging
from urllib.parse import quote
from datetime import timedelta

import requests
import yt_dlp
from flask import (Flask, Response, jsonify, render_template, request, 
                   send_from_directory, redirect, url_for, stream_with_context)

# ==========================================
# CONFIGURATION
# ==========================================
app = Flask(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, 'static')
VIDEO_DIR = os.path.join(STATIC_DIR, 'video')
UPLOAD_DIR = os.path.join(STATIC_DIR, 'uploads')

# Ensure directories exist
for path in [VIDEO_DIR, UPLOAD_DIR]:
    if not os.path.exists(path):
        try:
            os.makedirs(path)
        except: pass

# Global State
PROCESSING_STATUS = {
    "is_processing": False,
    "source_type": None,
    "input_source": None,
    "filename": None,
    "total_duration_str": "00:00",
    "total_duration_sec": 0,
    "current_offset": 0,
    "ffmpeg_process": None
}

# ==========================================
# BACKEND UTILS & PROCESSING LOGIC
# ==========================================

def clean_directory(directory):
    for filename in os.listdir(directory):
        file_path = os.path.join(directory, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception: pass

def get_media_info(input_path):
    cmd = ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', '-show_streams', '-select_streams', 'a', input_path]
    try:
        if input_path.startswith('http'):
            cmd.extend(['-user_agent', 'Mozilla/5.0'])
            
        res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        data = json.loads(res.stdout)
        
        duration_sec = float(data.get('format', {}).get('duration', 0))
        m, s = divmod(duration_sec, 60)
        h, m = divmod(m, 60)
        
        if h > 0:
            duration_str = f"{int(h)}:{int(m):02d}:{int(s):02d}"
        else:
            duration_str = f"{int(m):02d}:{int(s):02d}"
        
        return data.get('streams', []), duration_str, duration_sec
    except Exception as e: 
        print(f"Info Error: {e}")
        return [], "00:00", 0

def kill_ffmpeg():
    global PROCESSING_STATUS
    if PROCESSING_STATUS.get("ffmpeg_process"):
        proc = PROCESSING_STATUS["ffmpeg_process"]
        try:
            proc.terminate()
            try:
                proc.wait(timeout=2)
            except subprocess.TimeoutExpired:
                proc.kill()
        except Exception: pass
        finally:
            PROCESSING_STATUS["ffmpeg_process"] = None
            time.sleep(0.5)

def run_ffmpeg_process(input_source, output_manifest, start_time=0):
    global PROCESSING_STATUS
    PROCESSING_STATUS['is_processing'] = True
    
    if start_time > 0:
        clean_directory(VIDEO_DIR)

    audio_streams, _, _ = get_media_info(input_source)
    
    cmd = [
        'ffmpeg', '-y', '-loglevel', 'error',
    ]

    if input_source.startswith('http'):
        cmd.extend(['-user_agent', 'Mozilla/5.0'])
        cmd.extend(['-ss', str(start_time)]) 
        cmd.extend(['-i', input_source])
    else:
        cmd.extend(['-ss', str(start_time)])
        cmd.extend(['-i', input_source])

    cmd.extend([
        '-map', '0:v',
        '-c:v', 'libx264', '-crf', '23', '-preset', 'ultrafast', '-tune', 'zerolatency',
        '-force_key_frames', 'expr:gte(t,n_forced*4)', 
        '-threads', '0'
    ])

    if not audio_streams:
        cmd.extend(['-c:a', 'aac', '-b:a', '128k'])
    else:
        for i, stream in enumerate(audio_streams):
            lang = stream.get('tags', {}).get('language', 'und')
            cmd.extend([
                '-map', f'0:a:{i}',
                f'-c:a:{i}', 'aac', f'-b:a:{i}', '128k',
                f'-metadata:s:a:{i}', f'language={lang}'
            ])

    cmd.extend([
        '-f', 'dash',
        '-window_size', '50000', 
        '-extra_window_size', '50000',
        '-seg_duration', '4',
        '-use_template', '1',
        '-use_timeline', '1',
        '-init_seg_name', 'init-stream$RepresentationID$.m4s',
        '-media_seg_name', 'chunk-stream$RepresentationID$-$Number%05d$.m4s',
        output_manifest
    ])

    try:
        print(f"Starting FFmpeg on: {input_source}")
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        PROCESSING_STATUS["ffmpeg_process"] = proc
        proc.wait()
    except Exception as e:
        print(f"FFmpeg error: {e}")
    finally:
        PROCESSING_STATUS['is_processing'] = False

# ==========================================
# ROUTES
# ==========================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process_media():
    global PROCESSING_STATUS
    
    action_type = request.form.get('type')
    kill_ffmpeg()
    clean_directory(VIDEO_DIR)
    
    source_path = ""
    filename = "Stream"
    
    if action_type == 'file':
        clean_directory(UPLOAD_DIR)
        if 'file' not in request.files: return jsonify({'error': 'No file'}), 400
        file = request.files['file']
        if file.filename == '': return jsonify({'error': 'No filename'}), 400
        filename = file.filename
        source_path = os.path.join(UPLOAD_DIR, filename)
        file.save(source_path)
        PROCESSING_STATUS['source_type'] = 'local'

    elif action_type == 'url':
        raw_url = request.form.get('url')
        if not raw_url: return jsonify({'error': 'No URL'}), 400
        
        if 'drive.google.com' not in raw_url:
            return jsonify({'error': 'Invalid Source', 'message': 'Only Google Drive links are allowed.'}), 400

        try:
            ydl_opts = {'quiet': True, 'format': 'best', 'noplaylist': True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(raw_url, download=False)
                if 'entries' in info: info = info['entries'][0] 
                source_path = info.get('url') 
                filename = info.get('title', 'Web Stream')
                PROCESSING_STATUS['source_type'] = 'url'
        except Exception as e:
            return jsonify({'error': str(e), 'message': 'Failed to resolve URL'}), 400

    audio_streams, duration_str, duration_sec = get_media_info(source_path)

    PROCESSING_STATUS["filename"] = filename
    PROCESSING_STATUS["input_source"] = source_path
    PROCESSING_STATUS["total_duration_str"] = duration_str
    PROCESSING_STATUS["total_duration_sec"] = duration_sec
    PROCESSING_STATUS["current_offset"] = 0
    
    manifest_path = os.path.join(VIDEO_DIR, 'manifest.mpd')
    thread = threading.Thread(target=run_ffmpeg_process, args=(source_path, manifest_path, 0))
    thread.daemon = True 
    thread.start()

    return jsonify({
        'status': 'started', 
        'filename': filename, 
        'duration_str': duration_str,
        'duration_sec': duration_sec
    })

@app.route('/seek', methods=['POST'])
def seek_video():
    data = request.json
    target_time = float(data.get('timestamp', 0))
    source_path = PROCESSING_STATUS["input_source"]
    
    if not source_path: return jsonify({'error': 'No active file'}), 400

    kill_ffmpeg()
    manifest_path = os.path.join(VIDEO_DIR, 'manifest.mpd')
    thread = threading.Thread(target=run_ffmpeg_process, args=(source_path, manifest_path, target_time))
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'seeking', 'offset': target_time})

@app.route('/status')
def status():
    manifest_path = os.path.join(VIDEO_DIR, 'manifest.mpd')
    ready = os.path.exists(manifest_path)
    if ready:
        chunks = [f for f in os.listdir(VIDEO_DIR) if f.endswith('.m4s')]
        if len(chunks) < 2: ready = False

    return jsonify({
        'ready': ready,
        'processing': PROCESSING_STATUS['is_processing']
    })

@app.route('/manifest.mpd')
def serve_manifest():
    response = send_from_directory(VIDEO_DIR, 'manifest.mpd')
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    return response

@app.route('/<path:filename>')
def serve_segments(filename):
    return send_from_directory(VIDEO_DIR, filename)

if __name__ == '__main__':
    print("\n--- SERVER RUNNING: http://127.0.0.1:5000 ---\n")
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)

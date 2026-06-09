import yt_dlp
import subprocess
import os
import tempfile
from typing import List

def download_audio(video_url: str, output_dir: str) -> str:
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
    
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
        video_id = info_dict.get('id')
        ext = info_dict.get('ext', 'm4a')
        
    return os.path.join(output_dir, f"{video_id}.{ext}")

def convert_to_wav(input_path: str, output_path: str) -> str:
    command = [
        'ffmpeg',
        '-i', input_path,
        '-ac', '1',
        '-ar', '16000',
        '-y',
        '-loglevel', 'error',
        output_path
    ]
    
    subprocess.run(command, check=True)
    return output_path

def cleanup_temp_files(paths: List[str]):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

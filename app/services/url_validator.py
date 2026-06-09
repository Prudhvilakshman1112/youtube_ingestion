import re
from fastapi import HTTPException
from typing import Optional

YOUTUBE_URL_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

def extract_video_id(url: str) -> Optional[str]:
    match = YOUTUBE_URL_PATTERN.search(url)
    if match:
        return match.group(1)
    return None

def validate_url(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    return video_id

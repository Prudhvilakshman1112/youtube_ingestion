from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import Optional

def fetch_captions(video_id: str) -> Optional[str]:
    try:
        ytt_api = YouTubeTranscriptApi()
        try:
            transcript = ytt_api.get_transcript(video_id, languages=["en"])
        except (NoTranscriptFound, TranscriptsDisabled):
            transcript_list = ytt_api.list_transcripts(video_id)
            transcript = next(iter(transcript_list)).fetch()

        if transcript:
            return " ".join([item["text"] for item in transcript]).replace('\n', ' ')
        return None
        
    except Exception:
        return None

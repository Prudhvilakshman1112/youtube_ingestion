from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
from typing import Optional
import logging

logger = logging.getLogger(__name__)

def fetch_captions(video_id: str) -> Optional[str]:
    """Fetch captions/subtitles for a YouTube video.
    
    Uses youtube_transcript_api v1.x API:
    - ytt_api.fetch() to get transcript (replaces old get_transcript)
    - ytt_api.list() to list available transcripts (replaces old list_transcripts)
    - FetchedTranscript.snippets with .text attribute (replaces old list-of-dicts)
    """
    try:
        ytt_api = YouTubeTranscriptApi()
        try:
            # Try fetching English transcript directly
            transcript = ytt_api.fetch(video_id, languages=["en"])
        except (NoTranscriptFound, TranscriptsDisabled):
            # Fallback: list all available transcripts and grab the first one
            transcript_list = ytt_api.list(video_id)
            first_transcript = next(iter(transcript_list))
            transcript = first_transcript.fetch()

        if transcript and transcript.snippets:
            text = " ".join([snippet.text for snippet in transcript.snippets]).replace('\n', ' ')
            logger.info(f"Fetched {len(transcript.snippets)} caption segments for video {video_id}")
            return text
        return None
        
    except Exception as e:
        logger.warning(f"Caption fetch failed for video {video_id}: {type(e).__name__}: {e}")
        return None

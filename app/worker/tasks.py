import os
import tempfile
import logging
from celery import shared_task
from app.services.metadata_fetcher import get_video_metadata
from app.services.caption_fetcher import fetch_captions
from app.services.audio_pipeline import download_audio, convert_to_wav, cleanup_temp_files
from app.services.storage import upload_audio

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, acks_late=True)
def process_video_ingestion(self, video_url: str, video_id: str):
    scratch_dir = os.path.join(tempfile.gettempdir(), f"scratch_{video_id}")
    os.makedirs(scratch_dir, exist_ok=True)
    temp_files = []
    
    try:
        # Step 1: Metadata
        self.update_state(state='FETCHING_METADATA', meta={'progress': 'Fetching video metadata'})
        metadata = get_video_metadata(video_id)
        
        # Step 2: Try Captions first
        self.update_state(state='FETCHING_CAPTIONS', meta={'progress': 'Attempting to fetch captions'})
        captions = fetch_captions(video_id)
        
        s3_audio_uri = None
        
        # Step 3: If no captions, fallback to audio download
        if not captions:
            self.update_state(state='DOWNLOADING_AUDIO', meta={'progress': 'Downloading audio track'})
            audio_path = download_audio(video_url, scratch_dir)
            temp_files.append(audio_path)
            
            self.update_state(state='CONVERTING_AUDIO', meta={'progress': 'Converting to 16kHz WAV'})
            wav_path = os.path.join(scratch_dir, f"{video_id}.wav")
            convert_to_wav(audio_path, wav_path)
            temp_files.append(wav_path)
            
            self.update_state(state='UPLOADING', meta={'progress': 'Uploading to storage'})
            s3_audio_uri = upload_audio(wav_path, video_id)
            
        # Step 4: Stub for Module 4 (Transcription/Analysis)
        self.update_state(state='HANDOFF', meta={'progress': 'Passing to next module (stub)'})
        
        result = {
            "video_id": video_id,
            "metadata": metadata,
            "has_captions": bool(captions),
            "s3_audio_uri": s3_audio_uri,
            # We don't send full captions in result to avoid huge payloads in Celery backend
            "captions_extracted": bool(captions)
        }
        
        logger.info(f"Handoff data for M4: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(exc=exc, countdown=30)
    finally:
        cleanup_temp_files(temp_files)
        try:
            os.rmdir(scratch_dir)
        except OSError:
            pass # Directory might not be empty if something failed badly, ignore

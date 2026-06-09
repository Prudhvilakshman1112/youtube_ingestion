import os
import tempfile
import logging
from celery import shared_task
from app.services.metadata_fetcher import get_video_metadata
from app.services.caption_fetcher import fetch_captions
from app.services.audio_pipeline import download_audio, convert_to_wav, cleanup_temp_files
from app.services.storage import upload_audio, upload_transcript

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, acks_late=True)
def process_video_ingestion(self, video_url: str, video_id: str):
    scratch_dir = os.path.join(tempfile.gettempdir(), f"scratch_{video_id}")
    os.makedirs(scratch_dir, exist_ok=True)
    temp_files = []
    
    try:
        # Step 1: Fetch metadata
        self.update_state(state='FETCHING_METADATA', meta={'progress': 'Fetching video metadata'})
        metadata = get_video_metadata(video_id)
        
        # Step 2: Try to get existing captions from YouTube
        self.update_state(state='FETCHING_CAPTIONS', meta={'progress': 'Attempting to fetch captions'})
        captions = fetch_captions(video_id)
        
        s3_transcript_uri = None
        s3_audio_uri = None
        
        if captions:
            # --- PATH A: Captions found → store transcript text in S3 ---
            logger.info(f"Captions found for {video_id} ({len(captions)} chars). Uploading transcript to storage.")
            self.update_state(state='UPLOADING_TRANSCRIPT', meta={'progress': 'Uploading transcript to storage'})
            s3_transcript_uri = upload_transcript(captions, video_id)
            logger.info(f"Transcript uploaded: {s3_transcript_uri}")
        else:
            # --- PATH B: No captions → download audio and store in S3 ---
            logger.info(f"No captions for {video_id}. Falling back to audio download.")
            self.update_state(state='DOWNLOADING_AUDIO', meta={'progress': 'Downloading audio track'})
            audio_path = download_audio(video_url, scratch_dir)
            temp_files.append(audio_path)
            
            self.update_state(state='CONVERTING_AUDIO', meta={'progress': 'Converting to 16kHz WAV'})
            wav_path = os.path.join(scratch_dir, f"{video_id}.wav")
            convert_to_wav(audio_path, wav_path)
            temp_files.append(wav_path)
            
            self.update_state(state='UPLOADING_AUDIO', meta={'progress': 'Uploading audio to storage'})
            s3_audio_uri = upload_audio(wav_path, video_id)
            logger.info(f"Audio uploaded: {s3_audio_uri}")
            
        # Step 3: Complete
        self.update_state(state='COMPLETED', meta={'progress': 'Processing complete'})
        
        result = {
            "video_id": video_id,
            "metadata": metadata,
            "has_captions": bool(captions),
            "s3_transcript_uri": s3_transcript_uri,  # Set when captions were found
            "s3_audio_uri": s3_audio_uri,              # Set when audio was downloaded
        }
        
        logger.info(f"Processing complete for {video_id}: {result}")
        return result
        
    except Exception as exc:
        logger.error(f"Task failed for {video_id}: {exc}")
        self.retry(exc=exc, countdown=30)
    finally:
        cleanup_temp_files(temp_files)
        try:
            os.rmdir(scratch_dir)
        except OSError:
            pass


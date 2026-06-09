from fastapi import APIRouter, HTTPException
from typing import Any
from app.core.celery_app import celery_app
from app.schemas.video import VideoRequest, VideoMetadataResponse, ProcessResponse, TaskStatusResponse
from app.services.url_validator import validate_url
from app.services.metadata_fetcher import get_video_metadata
from app.services.caption_fetcher import fetch_captions
from app.worker.tasks import process_video_ingestion
from celery.result import AsyncResult

router = APIRouter()

@router.post("/validate", response_model=VideoMetadataResponse)
def validate_and_fetch_metadata(request: VideoRequest) -> Any:
    video_id = validate_url(request.url)
    
    try:
        metadata = get_video_metadata(video_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    has_captions = False
    try:
        captions = fetch_captions(video_id)
        has_captions = bool(captions)
    except Exception:
        pass
    
    metadata["has_captions"] = has_captions
    return metadata

@router.post("/process", response_model=ProcessResponse)
def start_processing(request: VideoRequest) -> Any:
    video_id = validate_url(request.url)
    task = process_video_ingestion.delay(request.url, video_id)
    return {"task_id": task.id}

@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> Any:
    task_result = AsyncResult(task_id, app=celery_app)
    
    return {
        "task_id": task_id,
        "state": task_result.state,
        "progress": task_result.info.get("progress") if isinstance(task_result.info, dict) else None,
        "result": task_result.result if task_result.state == "COMPLETED" else None
    }

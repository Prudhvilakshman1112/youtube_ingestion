# Module 3 — YouTube Ingestion Engineer

## Overview

This module is responsible for ingesting YouTube videos, validating URLs, extracting metadata, downloading audio when captions are unavailable, and passing the data to the next module. 
It includes a lightweight development setup with Redis and MinIO to run independently.

## Setup Instructions

1. Clone or ensure you are in the project directory.
2. Ensure you have Docker installed and running.
3. Make a copy of `.env.example` as `.env` and fill in your details (especially `YOUTUBE_API_KEY`).
4. Install FFmpeg and add it to your system PATH (required for audio conversion).

## How To Run (Phase A — Independent Development)

```bash
# 1. Start Redis + MinIO
docker-compose -f docker-compose.dev.yml up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start FastAPI server
uvicorn app.main:app --reload --port 8000

# 4. Start Celery worker (in a new terminal)
celery -A app.core.celery_app worker --loglevel=info --pool=solo

# 5. Run tests
pytest tests/ -v
```

## Integration with M1

When the shared repository is ready, refer to the project specs to copy files into the main `video-synopsis-ai/` repository, update requirements and env files, and adjust import paths.

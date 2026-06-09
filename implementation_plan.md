# Module 3 — YouTube Ingestion Engineer · Complete Build Plan

## How This Fits With M1 (DevOps)

> [!IMPORTANT]
> **You do NOT create the main Docker setup.** M1 owns `docker-compose.yml`, all Dockerfiles, Nginx, and the FastAPI skeleton. You write Python code that **plugs into** M1's structure.

### The Two-Phase Approach

```
Phase A (NOW)  → Build & test your code independently in d:\YouTube Ingestion\
Phase B (LATER) → Copy your files into M1's shared repo (video-synopsis-ai/)
```

### How Your Files Map to M1's Repo

| You Build (Phase A)                        | You Copy To (Phase B)                          |
|--------------------------------------------|------------------------------------------------|
| `app/api/v1/routes.py`                     | `backend/app/api/videos.py`                    |
| `app/services/url_validator.py`            | `backend/app/services/url_validator.py`         |
| `app/services/metadata_fetcher.py`         | `backend/app/services/metadata_fetcher.py`      |
| `app/services/caption_fetcher.py`          | `backend/app/services/caption_fetcher.py`       |
| `app/services/audio_pipeline.py`           | `backend/app/services/audio_pipeline.py`        |
| `app/services/storage.py`                  | `backend/app/services/storage.py`               |
| `app/worker/tasks.py`                      | `backend/app/tasks/ingestion.py`                |
| `app/schemas/video.py`                     | `backend/app/schemas/video.py`                  |
| Your packages in `requirements.txt`        | **Add** to M1's `backend/requirements.txt`      |
| Your env vars in `.env.example`            | **Add** to M1's `.env.example`                  |

### What M1 Provides That You Use (Don't Recreate)

- ❌ **Don't build**: Main `docker-compose.yml` with all 8 containers
- ❌ **Don't build**: Backend `Dockerfile`
- ❌ **Don't build**: Nginx, PostgreSQL, MongoDB, Flower setup
- ❌ **Don't build**: FastAPI `main.py` skeleton (M1 creates, you import into it)
- ✅ **You build**: A small `docker-compose.dev.yml` with **only Redis + MinIO** for testing

---

## Project Structure (Phase A — Your Independent Module)

```
d:\YouTube Ingestion\
├── docker-compose.dev.yml          # DEV ONLY: Redis + MinIO (for your testing)
├── .env.example                    # Your env vars (merge into M1's later)
├── .env                            # Local config (git-ignored)
├── requirements.txt                # Your Python packages only
├── README.md                       # Module documentation
│
├── app/
│   ├── __init__.py
│   ├── main.py                     # Temporary FastAPI app (for testing alone)
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py               # Pydantic settings (env vars)
│   │   └── celery_app.py           # Celery instance setup
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       └── routes.py           # Your REST endpoints
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── video.py                # Pydantic request/response models
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── url_validator.py        # Deliverable 1: URL validation
│   │   ├── metadata_fetcher.py     # Deliverable 2: YouTube Data API
│   │   ├── caption_fetcher.py      # Deliverable 3: youtube-transcript-api
│   │   ├── audio_pipeline.py       # Deliverable 4: yt-dlp + FFmpeg
│   │   └── storage.py              # Deliverable 5: S3/MinIO upload
│   │
│   └── worker/
│       ├── __init__.py
│       └── tasks.py                # Deliverable 6: Celery tasks
│
└── tests/
    ├── __init__.py
    ├── conftest.py                 # Shared test fixtures
    ├── test_url_validator.py
    ├── test_metadata_fetcher.py
    ├── test_caption_fetcher.py
    └── test_api.py
```

> [!NOTE]
> Your `app/main.py` is a **temporary** FastAPI app for testing your module independently. When you move to M1's repo, M1's `main.py` already exists — you just add your router import to it.

---

## User Review Required

> [!IMPORTANT]
> **YouTube Data API Key**: The code uses a placeholder `YOUR_YOUTUBE_API_KEY`. You need to create a Google Cloud project + enable "YouTube Data API v3" + generate an API key. Until then, the metadata fetcher will return errors, but all other components work.

> [!IMPORTANT]
> **FFmpeg on Windows**: Since you're running locally (not in M1's Docker), you need to [download FFmpeg for Windows](https://www.gyan.dev/ffmpeg/builds/) and add it to your system PATH. The audio pipeline needs it.

> [!WARNING]
> **yt-dlp rate limiting**: YouTube may throttle downloads from cloud IPs. For dev/testing, local is most reliable.

---

## Open Questions

> [!IMPORTANT]
> **Max video duration**: Your spec says 3 hours. I'll default to `MAX_VIDEO_DURATION_MINUTES=180`. Should this be different?

> [!IMPORTANT]
> **Module 4 handoff**: M4 doesn't exist yet. I'll create a **stub task** that logs the handoff data. When M4 is ready, you replace it with their real task. Good?

> [!IMPORTANT]
> **Storage bucket name**: I'll use `video-synopsis-audio`. The system auto-creates it on startup. Confirm or change?

---

## Proposed Changes

### Dev Infrastructure (Lightweight — Just For Your Testing)

#### [NEW] [docker-compose.dev.yml](file:///d:/YouTube%20Ingestion/docker-compose.dev.yml)
- **Only 2 services**: `redis` (:6379) and `minio` (:9000/:9001)
- You run FastAPI and Celery worker **locally on Windows** with Python
- This avoids needing M1's full Docker setup during development
- Start with: `docker-compose -f docker-compose.dev.yml up -d`

#### [NEW] [.env.example](file:///d:/YouTube%20Ingestion/.env.example)
- Your module's env vars only: `YOUTUBE_API_KEY`, `REDIS_URL`, `MINIO_*`
- When M1's repo is ready, you add these lines to M1's `.env.example`

#### [NEW] [.env](file:///d:/YouTube%20Ingestion/.env)
- Dev defaults: MinIO local creds, Redis localhost, placeholder API key

#### [NEW] [requirements.txt](file:///d:/YouTube%20Ingestion/requirements.txt)
- `fastapi`, `uvicorn[standard]`, `pydantic-settings`
- `google-api-python-client`, `youtube-transcript-api`, `yt-dlp`
- `boto3`, `celery[redis]`, `redis`
- `isodate`, `pytest`, `httpx` (for testing)

---

### Core Configuration

#### [NEW] [config.py](file:///d:/YouTube%20Ingestion/app/core/config.py)
- Uses Pydantic v2 `BaseSettings` with **`SettingsConfigDict`** (not the legacy `class Config` inner class)
- Explicit `env_file=".env"`, `env_file_encoding="utf-8"`, `extra="ignore"`
- All settings: `YOUTUBE_API_KEY`, `REDIS_URL`, `MINIO_*`, `MAX_VIDEO_DURATION_MINUTES`
- Single source of truth — imported by both FastAPI and Celery
```python
# Pattern used:
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
```

#### [NEW] [celery_app.py](file:///d:/YouTube%20Ingestion/app/core/celery_app.py)
- Celery instance configured with Redis broker + backend
- Task autodiscovery from `app.worker.tasks`
- **Critical**: Enables `task_track_started=True` and `result_extended=True` so custom states (`FETCHING_METADATA`, `DOWNLOADING_AUDIO`, etc.) are visible to the frontend via `/status/{task_id}` — without this, the frontend only sees `PENDING` until task fully completes
```python
# Required config:
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)
```

---

### FastAPI Application & API Routes

#### [NEW] [main.py](file:///d:/YouTube%20Ingestion/app/main.py)
- Temporary standalone FastAPI app (for testing without M1)
- CORS middleware, health check, v1 router included
- Startup event: ensures MinIO bucket exists
- **When merging with M1**: Just add `app.include_router(video_router)` to M1's main.py

#### [NEW] [routes.py](file:///d:/YouTube%20Ingestion/app/api/v1/routes.py)
Three endpoints matching the project API spec:

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/videos/validate` | Validates URL + returns metadata |
| `POST` | `/api/v1/videos/process` | Starts async pipeline, returns `task_id` |
| `GET` | `/api/v1/videos/status/{task_id}` | Returns task state + result |

#### [NEW] [video.py](file:///d:/YouTube%20Ingestion/app/schemas/video.py)
- `VideoRequest` — input schema (`url: str`)
- `VideoMetadataResponse` — title, channel, duration, thumbnail, has_captions
- `ProcessResponse` — returns `task_id`
- `TaskStatusResponse` — state, progress, result

---

### Service Layer — The 6 Deliverables

#### Deliverable 1: [NEW] [url_validator.py](file:///d:/YouTube%20Ingestion/app/services/url_validator.py)
- `extract_video_id(url) → str | None` — regex supporting all formats:
  - `youtube.com/watch?v=ID`, `youtu.be/ID`, `youtube.com/embed/ID`, `youtube.com/shorts/ID`, `m.youtube.com/watch?v=ID`
- `validate_url(url) → str` — extracts ID or raises `HTTPException(400)`

#### Deliverable 2: [NEW] [metadata_fetcher.py](file:///d:/YouTube%20Ingestion/app/services/metadata_fetcher.py)
- `get_video_metadata(video_id) → dict` — YouTube Data API v3
- Returns: `title`, `channel_name`, `duration_seconds`, `thumbnail_url`, `is_public`
- Parses ISO 8601 duration with `isodate`
- Error handling: not found (404), private (403), over duration limit (400)

#### Deliverable 3: [NEW] [caption_fetcher.py](file:///d:/YouTube%20Ingestion/app/services/caption_fetcher.py)
- `fetch_captions(video_id) → str | None`
- Uses **new instance-based API** (2026 pattern): `YouTubeTranscriptApi()` then `.get_transcript(video_id)` — static methods were removed in early 2026
- Tries `languages=["en"]` first, then falls back to any available language
- Returns `None` on `TranscriptsDisabled` / `NoTranscriptFound` → triggers audio fallback
```python
# Correct 2026 pattern (static methods are REMOVED):
ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.get_transcript(video_id, languages=["en"])
```

#### Deliverable 4: [NEW] [audio_pipeline.py](file:///d:/YouTube%20Ingestion/app/services/audio_pipeline.py)
- `download_audio(video_url, output_dir) → str` — yt-dlp audio-only download
- `convert_to_wav(input_path, output_path) → str` — FFmpeg: 16kHz mono WAV
- `cleanup_temp_files(paths)` — removes intermediates

#### Deliverable 5: [NEW] [storage.py](file:///d:/YouTube%20Ingestion/app/services/storage.py)
- `get_s3_client()` — boto3 configured for MinIO
- `ensure_bucket_exists(bucket)` — auto-creates on startup
- `upload_audio(file_path, video_id) → str` — returns `s3://` path

#### Deliverable 6: [NEW] [tasks.py](file:///d:/YouTube%20Ingestion/app/worker/tasks.py)
- `process_video_ingestion(video_url, video_id)` — main Celery task
  - `bind=True, max_retries=3, acks_late=True`
  - Flow: metadata → captions → (if none) audio download → convert → upload → trigger M4 stub
  - Custom state updates: `FETCHING_METADATA`, `FETCHING_CAPTIONS`, `DOWNLOADING_AUDIO`, `CONVERTING_AUDIO`, `UPLOADING`, `COMPLETED`
  - Retry with `countdown=30` on failure
  - **Cross-platform temp paths**: Uses `tempfile.gettempdir()` instead of hardcoded `/tmp/` — prevents `FileNotFoundError` on Windows during Phase A local development
  - Cleanup in `finally` block to prevent disk leaks
```python
# Cross-platform scratch directory:
import tempfile
scratch_dir = os.path.join(tempfile.gettempdir(), f"scratch_{video_id}")
```

---

### Tests

#### [NEW] [test_url_validator.py](file:///d:/YouTube%20Ingestion/tests/test_url_validator.py)
- All valid URL formats, invalid URLs, edge cases

#### [NEW] [test_metadata_fetcher.py](file:///d:/YouTube%20Ingestion/tests/test_metadata_fetcher.py)
- Mocked YouTube API: valid video, private, not found, over limit

#### [NEW] [test_caption_fetcher.py](file:///d:/YouTube%20Ingestion/tests/test_caption_fetcher.py)
- Mocked transcript API: found, not found, disabled

#### [NEW] [test_api.py](file:///d:/YouTube%20Ingestion/tests/test_api.py)
- Integration tests for all 3 endpoints

---

### Documentation

#### [NEW] [README.md](file:///d:/YouTube%20Ingestion/README.md)
- Module overview, setup instructions, data contract (what you pass to M4)
- "How to merge into M1's repo" section with step-by-step instructions

---

## Integration Checklist — When M1's Repo is Ready

When M1 pushes the shared `video-synopsis-ai/` repo, follow these steps:

1. Clone M1's repo
2. Copy your `app/services/*.py` → `backend/app/services/`
3. Copy your `app/worker/tasks.py` → `backend/app/tasks/ingestion.py`
4. Copy your `app/api/v1/routes.py` → `backend/app/api/videos.py`
5. Copy your `app/schemas/video.py` → `backend/app/schemas/video.py`
6. **Add** your packages to M1's `backend/requirements.txt`
7. **Add** your env vars to M1's `.env.example`
8. Update import paths if M1's package structure differs slightly
9. Add `from app.api.videos import router as video_router` to M1's `main.py`
10. Test: `docker-compose up --build` → hit your endpoints

---

## How To Run (Phase A — Independent Development)

```bash
# 1. Start Redis + MinIO (only 2 containers — lightweight)
docker-compose -f docker-compose.dev.yml up -d

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Start FastAPI server
uvicorn app.main:app --reload --port 8000

# 4. Start Celery worker (in a new terminal)
celery -A app.core.celery_app worker --loglevel=info --pool=solo

# 5. Test: open http://localhost:8000/docs in browser

# 6. Run tests
pytest tests/ -v
```

---

## Verification Plan

### Automated Tests
```bash
pytest tests/ -v
```

### Manual Verification
1. `docker-compose -f docker-compose.dev.yml up -d` → Redis + MinIO running
2. `GET http://localhost:8000/health` → `{"status": "ok"}`
3. `POST http://localhost:8000/api/v1/videos/validate` with `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}`
4. `POST http://localhost:8000/api/v1/videos/process` → returns `task_id`
5. `GET http://localhost:8000/api/v1/videos/status/{task_id}` → shows progress
6. MinIO console at `http://localhost:9001` → verify audio files uploaded
7. Celery worker terminal → verify task execution and M4 stub handoff

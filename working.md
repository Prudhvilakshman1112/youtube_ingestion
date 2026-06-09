# YouTube Ingestion Module - Execution & Integration Guide

This guide provides a step-by-step walkthrough to run, test, and eventually integrate the YouTube Ingestion module.

## Phase A: Independent Execution (Run it right now)

Follow these chronological steps to test this module locally on your machine.

### Step 1: Configure Credentials (`.env` file)
Open the `.env` file located at `d:\YouTube Ingestion\.env`. You need to ensure the following variables are set:

```env
# 1. YouTube Data API v3 Key (CRITICAL)
# You MUST get this from Google Cloud Console. 
# Go to https://console.cloud.google.com/ -> Create Project -> Enable "YouTube Data API v3" -> Credentials -> Create API Key
YOUTUBE_API_KEY=your_actual_api_key_here

# 2. Redis Configuration (Leave as default for local testing)
REDIS_URL=redis://localhost:6379/0

# 3. MinIO/S3 Storage Configuration (Leave as default for local testing)
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=video-synopsis-audio

# 4. Business Logic (Adjust if needed)
MAX_VIDEO_DURATION_MINUTES=180
```

### Step 2: Install FFmpeg (Required for Audio Processing)
Since you are on Windows and running this locally:
1. Download FFmpeg from [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) (get the `ffmpeg-git-full.7z` or `.zip`).
2. Extract it to a folder (e.g., `C:\ffmpeg`).
3. Add `C:\ffmpeg\bin` to your System's Environment Variables `PATH`.
4. Open a new terminal and type `ffmpeg -version` to verify it works.

### Step 3: Start Infrastructure Services
You need Docker Desktop running. Open a terminal in `d:\YouTube Ingestion` and run:
```bash
docker-compose -f docker-compose.dev.yml up -d
```
*This starts Redis (for Celery tasks) and MinIO (for local S3 storage).*

### Step 4: Start the FastAPI Server
Open a terminal in `d:\YouTube Ingestion` and run:
```bash
# Activate your virtual environment if you haven't
.\venv\Scripts\activate

# Start the server
uvicorn app.main:app --reload --port 8000
```

### Step 5: Start the Celery Background Worker
Open a **new** terminal in `d:\YouTube Ingestion` and run:
```bash
# Activate your virtual environment
.\venv\Scripts\activate

# Start the Celery worker
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

### Step 6: Test the API Flow
1. Open your browser and go to the Swagger UI: **http://localhost:8000/docs**
2. **Test `/api/v1/videos/validate`**:
   - Click "Try it out".
   - Enter a URL: `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}`
   - Execute. You should see metadata (Title, duration, etc.) plus `has_captions: true` and the `captions_text` field with the full transcript.
3. **Test `/api/v1/videos/process`**:
   - Click "Try it out".
   - Enter a URL: `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}`
   - Execute. It will return a `task_id` (e.g., `13cd5d6f...`).
4. **Test `/api/v1/videos/status/{task_id}`**:
   - Copy the `task_id` from the previous step.
   - Paste it into the `task_id` field and execute.
   - You will see the state change (`FETCHING_METADATA` -> `FETCHING_CAPTIONS` -> `UPLOADING_TRANSCRIPT` or `DOWNLOADING_AUDIO` -> `SUCCESS`).
   - The result will contain either `s3_transcript_uri` (if captions existed) or `s3_audio_uri` (if audio was downloaded).
5. **Verify Storage Upload**:
   - Open **http://localhost:9001** in your browser.
   - Login with `minioadmin` / `minioadmin`.
   - Go to Object Browser -> `video-synopsis-audio`.
   - **If the video had captions:** Check `transcripts/` folder — you should see a `.txt` file!
   - **If the video had no captions:** Check `audio/` folder — you should see a `.wav` file!

---

## Phase B: Integration into Complete Project (M1 Handoff)

Once you are satisfied that Phase A works perfectly, you need to migrate this code into the main monolithic repository (managed by the M1 DevOps team).

### Step 1: Clone the Main Repo
Clone the main project repository (e.g., `video-synopsis-ai/`) that M1 provides.

### Step 2: Copy the Files Over
Copy your code into the monolithic backend structure:
- Copy contents of `d:\YouTube Ingestion\app\services\` to `video-synopsis-ai\backend\app\services\`
- Copy `d:\YouTube Ingestion\app\worker\tasks.py` to `video-synopsis-ai\backend\app\tasks\ingestion.py`
- Copy `d:\YouTube Ingestion\app\api\v1\routes.py` to `video-synopsis-ai\backend\app\api\videos.py`
- Copy `d:\YouTube Ingestion\app\schemas\video.py` to `video-synopsis-ai\backend\app\schemas\video.py`

*(Note: You do NOT copy `docker-compose.dev.yml` or `main.py` because M1 already built the production versions of those).*

### Step 3: Update Dependencies & Env Vars
1. Open `video-synopsis-ai\backend\requirements.txt` and add:
   ```text
   google-api-python-client>=2.0.0
   youtube-transcript-api>=0.6.0
   yt-dlp>=2023.0.0
   boto3>=1.28.0
   isodate>=0.6.0
   ```
2. Open `video-synopsis-ai\.env` (and `.env.example`) and append your variables:
   ```env
   YOUTUBE_API_KEY=your_actual_api_key_here
   MAX_VIDEO_DURATION_MINUTES=180
   ```

### Step 4: Register Your Router in the Main App
Open the main `video-synopsis-ai\backend\app\main.py` file and add:
```python
from app.api.videos import router as video_router

# Inside the app setup
app.include_router(video_router, prefix="/api/v1/videos", tags=["videos"])
```

### Step 5: Test the Full Monolith
Run the full project using M1's docker setup:
```bash
docker-compose up --build
```
Your endpoints will now be live as part of the complete architecture!

# Module 3 — YouTube Ingestion Engine: Complete Project Report

> **Audience:** Someone with zero prior knowledge of this project.
> **Purpose:** This document is the single source of truth for everything about this module — what it does, how it was built, why specific technologies were chosen over alternatives, how every line of code works, how to run it, how to test it, and how it integrates into the larger product.

---

# Table of Contents

1. [What is This Project?](#1-what-is-this-project)
2. [The Bigger Picture — Where This Module Fits](#2-the-bigger-picture--where-this-module-fits)
3. [Project Directory Structure](#3-project-directory-structure)
4. [Technology Stack — What We Used and Why](#4-technology-stack--what-we-used-and-why)
5. [Environment Variables — The `.env` File Explained](#5-environment-variables--the-env-file-explained)
6. [Dependencies — The `requirements.txt` Explained](#6-dependencies--the-requirementstxt-explained)
7. [Docker — What It Is, Why We Use It, and Every Command Explained](#7-docker--what-it-is-why-we-use-it-and-every-command-explained)
8. [Running Without Docker — Alternatives and Problems](#8-running-without-docker--alternatives-and-problems)
9. [Code Deep-Dive — Every File Explained Line by Line](#9-code-deep-dive--every-file-explained-line-by-line)
10. [The Complete Data Flow — Visual Walkthrough](#10-the-complete-data-flow--visual-walkthrough)
11. [Phase A — Local Development and Testing](#11-phase-a--local-development-and-testing)
12. [Phase B — Integration into the Complete Project](#12-phase-b--integration-into-the-complete-project)
13. [Testing — How We Verified Everything Works](#13-testing--how-we-verified-everything-works)
14. [Errors We Encountered and How We Fixed Them](#14-errors-we-encountered-and-how-we-fixed-them)
15. [Glossary of Terms](#15-glossary-of-terms)

---

# 1. What is This Project?

## The Problem

Imagine you have a YouTube video and you want an AI to summarise it. The AI cannot "watch" the video — it can only read text. So someone needs to convert that YouTube video into text first. That is what this module does.

## The Solution

This module is called **Module 3: The YouTube Ingestion Engine**. When a user gives us a YouTube URL, we:

1. **Validate** the URL — confirm it is a real YouTube link and extract the unique Video ID.
2. **Fetch Metadata** — call YouTube's official API to get the video title, channel name, duration, and thumbnail.
3. **Try Captions First** — check if the video has subtitles/captions already available (many YouTube videos have auto-generated captions). If yes, we grab the text directly — no need to download any audio.
4. **Fallback to Audio** — if captions do not exist, we download the audio track of the video.
5. **Convert Audio** — convert the downloaded audio into a specific format (16kHz, mono channel, `.wav` file) that speech-to-text AI models require.
6. **Upload to Storage** — upload the `.wav` file to a cloud-compatible storage bucket (MinIO/S3).
7. **Hand Off** — pass all the collected data (metadata, captions or audio file location) to the next module (Module 4: Transcription) which will convert the audio to text.

## Why "Ingestion"?

The word "ingestion" means "taking something in". In data engineering, it means taking raw data from an external source (YouTube) and bringing it into your system in a usable format. We are "ingesting" YouTube videos.

---

# 2. The Bigger Picture — Where This Module Fits

This module is **one piece of a larger application** called `video-synopsis-ai`. The full application has multiple modules, each built by different team members:

```mermaid
flowchart LR
    subgraph "video-synopsis-ai (Full Application)"
        M1["Module 1\nDevOps\n(Docker, Nginx,\nDatabases)"]
        M3["Module 3\nYouTube Ingestion\n(THIS MODULE)"]
        M4["Module 4\nTranscription\n(Speech-to-Text)"]
        M5["Module 5\nSummarisation\n(AI Summary)"]
        FE["Frontend\n(React/Next.js\nUser Interface)"]
    end

    FE -->|"User submits URL"| M3
    M3 -->|"Audio file + Metadata"| M4
    M4 -->|"Transcript text"| M5
    M5 -->|"Summary"| FE
    M1 -.->|"Hosts everything"| M3
    M1 -.->|"Hosts everything"| M4
    M1 -.->|"Hosts everything"| M5
```

**Module 1 (DevOps)** — Builds the infrastructure: Docker containers, Nginx reverse proxy, PostgreSQL/MongoDB databases, and the main FastAPI skeleton. They own the production server.

**Module 3 (YouTube Ingestion — THIS IS US)** — Takes a YouTube URL, extracts everything useful from it (metadata, captions, audio), and passes it forward.

**Module 4 (Transcription)** — Takes the audio file we uploaded and converts it to text using AI speech-to-text models like OpenAI Whisper.

**Module 5 (Summarisation)** — Takes the transcript and generates a human-readable summary using Large Language Models (LLMs).

**Frontend** — The user-facing web application where someone pastes a YouTube URL and eventually sees the summary.

### The Two-Phase Approach

Because all these modules are built by different people, we cannot wait for everyone else to finish before we start testing our own code. So we use two phases:

- **Phase A (NOW)**: Build and test our code *independently* in our own folder (`d:\YouTube Ingestion\`). We spin up our own mini infrastructure using Docker.
- **Phase B (LATER)**: When M1's shared repository is ready, we copy our tested code into it and plug into the full system.

---

# 3. Project Directory Structure

Here is every file and folder in the project, with a description of what each one does:

```
d:\YouTube Ingestion\
│
├── docker-compose.dev.yml      ← Docker file to start Redis + MinIO (Phase A only)
├── .env.example                ← Template showing what environment variables are needed
├── .env                        ← Actual environment variables with real values (git-ignored)
├── requirements.txt            ← List of Python packages this project needs
├── README.md                   ← Quick-start instructions
├── working.md                  ← Step-by-step execution guide (Phase A + Phase B)
├── knowledge.md                ← THIS FILE — complete project documentation
│
├── app/                        ← All application source code lives here
│   ├── __init__.py             ← Makes "app" a Python package (required by Python)
│   │
│   ├── main.py                 ← The entry point — starts the FastAPI web server
│   │
│   ├── core/                   ← Core configuration files
│   │   ├── __init__.py         ← Makes "core" a Python package
│   │   ├── config.py           ← Loads environment variables into Python
│   │   └── celery_app.py       ← Initialises the Celery background task system
│   │
│   ├── api/                    ← API endpoint definitions
│   │   ├── __init__.py         ← Makes "api" a Python package
│   │   └── v1/                 ← Version 1 of the API
│   │       ├── __init__.py     ← Makes "v1" a Python package
│   │       └── routes.py       ← The 3 HTTP endpoints (/validate, /process, /status)
│   │
│   ├── schemas/                ← Data shape definitions (what the API expects/returns)
│   │   ├── __init__.py         ← Makes "schemas" a Python package
│   │   └── video.py            ← Pydantic models for request/response validation
│   │
│   ├── services/               ← Business logic — the actual work happens here
│   │   ├── __init__.py         ← Makes "services" a Python package
│   │   ├── url_validator.py    ← Validates YouTube URLs and extracts Video IDs
│   │   ├── metadata_fetcher.py ← Calls YouTube Data API v3 for video details
│   │   ├── caption_fetcher.py  ← Tries to fetch subtitles/captions from YouTube
│   │   ├── audio_pipeline.py   ← Downloads audio (yt-dlp) and converts it (FFmpeg)
│   │   └── storage.py          ← Uploads files to MinIO/S3 cloud storage
│   │
│   └── worker/                 ← Background task definitions
│       ├── __init__.py         ← Makes "worker" a Python package
│       └── tasks.py            ← The Celery task that orchestrates the full pipeline
│
├── tests/                      ← Automated test files
│   ├── __init__.py             ← Makes "tests" a Python package
│   ├── conftest.py             ← Shared test fixtures (like a reusable test client)
│   ├── test_url_validator.py   ← Tests for URL validation
│   ├── test_metadata_fetcher.py← Tests for metadata fetching
│   ├── test_caption_fetcher.py ← Tests for caption fetching
│   └── test_api.py             ← Integration tests for all 3 API endpoints
│
└── venv/                       ← Python virtual environment (auto-generated, git-ignored)
```

### What are all those `__init__.py` files?

Python requires a file called `__init__.py` inside every folder that you want to treat as a "package" (a collection of related modules). Without it, Python would not recognize `app.services.url_validator` as a valid import path. These files can be empty — their mere existence is what matters.

---

# 4. Technology Stack — What We Used and Why

## 4.1 Python (Programming Language)

**What it is:** Python is a general-purpose programming language known for its readability and massive ecosystem of libraries.

**Why we chose it:**
- The entire `video-synopsis-ai` project uses Python for its backend.
- Python has the best ecosystem for AI/ML tasks (which Modules 4 and 5 need).
- Libraries like `yt-dlp`, `youtube-transcript-api`, and `boto3` are Python-native.
- FastAPI (our web framework) is Python-based.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **Node.js (JavaScript)** | Weaker AI/ML ecosystem. The rest of the team uses Python. |
| **Go** | Very fast, but fewer YouTube-related libraries available. |
| **Java** | Too verbose for rapid prototyping. Overkill for this use case. |

---

## 4.2 FastAPI (Web Framework)

**What it is:** FastAPI is a modern, high-performance web framework for building APIs with Python. It automatically generates interactive API documentation (Swagger UI) at `/docs`.

**Why we chose it:**
- **Automatic Documentation**: You get a fully interactive API testing page at `http://localhost:8000/docs` for free. This is how you tested the endpoints in your browser.
- **Data Validation**: Uses Pydantic to automatically validate incoming data. If someone sends a request without a `url` field, FastAPI automatically returns a `422 Validation Error` — we don't need to write that check manually.
- **Async Support**: Can handle thousands of simultaneous requests without blocking.
- **Type Hints**: Python type annotations become self-documenting API contracts.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **Flask** | Older, slower, no built-in data validation, no auto-generated docs. |
| **Django** | Too heavy — it includes an ORM, admin panel, templating engine we don't need. |
| **Express.js** | JavaScript-based. Doesn't fit the Python ecosystem. |

**The command to start it:**
```bash
uvicorn app.main:app --reload --port 8000
```

Breaking this command down word by word:
- `uvicorn` — The ASGI server that actually runs FastAPI (FastAPI itself is just a framework; uvicorn is the server that serves it over HTTP).
- `app.main:app` — Tells uvicorn: "Go to the `app` folder, then `main.py`, and find the variable called `app`" (which is our FastAPI instance).
- `--reload` — Automatically restart the server whenever you save a code change. Only used during development.
- `--port 8000` — Listen on port 8000. You access it via `http://localhost:8000`.

**What this command returns/does:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [66080] using WatchFiles
INFO:     Started server process [31128]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```
This means the server is running and ready to accept HTTP requests.

---

## 4.3 Celery (Background Task Queue)

**What it is:** Celery is a distributed task queue for Python. It lets you run heavy, time-consuming jobs in the background so the user doesn't have to wait.

**Why we need background tasks:**
When a user clicks "Process Video", downloading audio can take 5-30 seconds (or more for long videos). If we did this inside the FastAPI request handler, the user's browser would show a loading spinner for 30+ seconds and might even time out. Instead:
1. FastAPI receives the request.
2. FastAPI tells Celery: "Hey, process this video in the background."
3. FastAPI immediately returns a `task_id` to the user (takes <100ms).
4. The user can poll `/status/{task_id}` to check progress.
5. Celery processes the video independently in a separate process.

**Why we chose Celery:**
- Industry standard for Python background tasks.
- Built-in retry mechanism (if a task fails, Celery automatically retries it up to 3 times).
- Custom state tracking (we can update the state to `FETCHING_METADATA`, `DOWNLOADING_AUDIO`, etc. and the frontend can show a progress indicator).
- Works with Redis as both message broker and result backend.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **Python `threading`** | No retry mechanism, no state tracking, no persistence. If the server crashes, all tasks are lost. |
| **RQ (Redis Queue)** | Simpler but lacks Celery's custom states and retry logic. |
| **Dramatiq** | Good alternative but smaller community. Celery has more tutorials and Stack Overflow answers. |
| **Huey** | Lightweight but lacks advanced features like task chaining. |

**The command to start the Celery worker:**
```bash
celery -A app.core.celery_app worker --loglevel=info --pool=solo
```

Breaking this command down word by word:
- `celery` — The Celery command-line tool.
- `-A app.core.celery_app` — Tells Celery: "The application instance is in `app/core/celery_app.py`, use the variable called `celery_app`."
- `worker` — Start a worker process (the thing that actually picks up and executes tasks).
- `--loglevel=info` — Show informational log messages (so we can see when tasks start, succeed, or fail).
- `--pool=solo` — **Critical for Windows.** Celery's default pool is `prefork` (uses multiple processes), which doesn't work on Windows. The `solo` pool runs tasks one at a time in the main process. In production (Linux/Docker), this flag is not needed.

**What this command returns/does:**
```
 -------------- celery@prudhvi v5.6.3 (recovery)
--- ***** -----
-- ******* ---- Windows-11-10.0.26100-SP0
- *** --- * ---
- ** ---------- [config]
- ** ---------- .> app:         worker:0x26d90cc9d30
- ** ---------- .> transport:   redis://localhost:6379/0
- ** ---------- .> results:     redis://localhost:6379/0
- *** --- * --- .> concurrency: 12 (solo)
-- ******* ---- .> task events: OFF
--- ***** -----
```
This means the worker is connected to Redis and waiting for tasks.

---

## 4.4 Redis (Message Broker & Result Backend)

**What it is:** Redis is an in-memory key-value database. It is extremely fast because it stores everything in RAM (memory) instead of on disk.

**Two roles Redis plays in our project:**
1. **Message Broker:** When FastAPI calls `process_video_ingestion.delay(...)`, Celery serializes the task into a message and pushes it into a Redis queue. The Celery worker pops messages from this queue and executes them. Think of Redis as a "mailbox" between FastAPI and Celery.
2. **Result Backend:** When a Celery task finishes, it stores the result (success/failure, return value) back into Redis. When the user calls `/status/{task_id}`, we look up the result in Redis.

**Why we chose Redis:**
- Blazing fast (sub-millisecond reads/writes).
- Can serve as both broker and backend (one service instead of two).
- Simple to set up via Docker.
- Native support in Celery (just install `celery[redis]`).

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **RabbitMQ** | More powerful message broker, but heavier to set up and overkill for our use case. |
| **Amazon SQS** | Cloud-only, adds cost and complexity for local development. |
| **PostgreSQL as broker** | Possible but much slower than Redis for message passing. |

**How Redis runs in our project:**
Redis runs as a Docker container (see Section 7). It listens on port `6379` (the standard Redis port). Our code connects to it via `redis://localhost:6379/0` (database 0).

---

## 4.5 MinIO (Object Storage / S3-Compatible)

**What it is:** MinIO is an open-source object storage server that is API-compatible with Amazon S3. "Object storage" means it stores files (like audio files) in "buckets" (like folders) and gives each file a unique URL.

**Why we need it:**
After downloading and converting the YouTube audio to `.wav`, we need to store it somewhere that Module 4 can access. We can't just leave it on our local hard drive — in production, different modules run on different servers. Object storage provides a central, accessible location.

**Why MinIO specifically (instead of real AWS S3):**
- We're developing locally. Using real AWS S3 would require an AWS account, cost money, and need internet for every test.
- MinIO runs locally via Docker and speaks the exact same API language as S3. So our code uses `boto3` (the AWS SDK) to talk to MinIO, and when we move to production, the same code works with real S3 without any changes — we just change the endpoint URL in `.env`.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **AWS S3** | Costs money, requires internet, requires AWS account. Fine for production, overkill for local development. |
| **Local filesystem** | Works locally but breaks in production where modules run on different machines. |
| **Google Cloud Storage** | Same as S3 — cloud-only, costs money. |
| **Azure Blob Storage** | Same issue. |

**MinIO has two ports:**
- Port `9000` — The S3 API endpoint (our code talks to this).
- Port `9001` — The web-based admin console (you can open `http://localhost:9001` in your browser, log in with `minioadmin/minioadmin`, and visually browse uploaded files).

---

## 4.6 yt-dlp (YouTube Audio Downloader)

**What it is:** `yt-dlp` is a command-line tool and Python library for downloading videos/audio from YouTube and thousands of other sites. It is the maintained fork of the older `youtube-dl` project.

**Why we chose it:**
- Most actively maintained YouTube downloader (frequent updates to handle YouTube changes).
- Can download audio-only (no need to download the full video).
- Supports format selection (`m4a/bestaudio/best`).
- Python-native API — we can use it as a library, not just a command-line tool.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **youtube-dl** | The original project. Largely abandoned, rarely updated, breaks frequently with YouTube changes. |
| **pytube** | Simpler but less reliable, breaks more often, fewer format options. |
| **Direct YouTube iframe API** | Only for embedding videos in web pages, cannot download audio. |

---

## 4.7 FFmpeg (Audio Converter)

**What it is:** FFmpeg is a free, open-source multimedia framework that can convert audio/video between virtually any format. It is a system-level tool (not a Python package) that must be installed separately.

**Why we need it:**
`yt-dlp` downloads audio in whatever format YouTube provides (usually `.m4a` or `.webm`). But AI speech-to-text models (like OpenAI Whisper) require audio in a very specific format:
- **16kHz sample rate** (16,000 samples per second) — speech recognition models are trained on this rate.
- **Mono channel** (single audio channel) — stereo is unnecessary for speech.
- **WAV format** — uncompressed audio that AI models can read directly.

**The FFmpeg command we use:**
```bash
ffmpeg -i input.m4a -ac 1 -ar 16000 -y -loglevel error output.wav
```
- `-i input.m4a` — Input file.
- `-ac 1` — Audio channels = 1 (mono).
- `-ar 16000` — Audio sample rate = 16000 Hz.
- `-y` — Overwrite output file if it already exists (no interactive prompt).
- `-loglevel error` — Only show errors, not informational messages.
- `output.wav` — Output file in WAV format.

**Alternatives considered:**
| Alternative | Why We Didn't Use It |
|---|---|
| **pydub** | Python library that wraps FFmpeg. Adds an unnecessary layer — we'd still need FFmpeg installed. |
| **librosa** | Python library for audio analysis. Can load audio but not optimised for format conversion. |
| **sox** | Another audio tool, but FFmpeg is more universal and better documented. |

---

## 4.8 YouTube Data API v3 (Metadata)

**What it is:** Google's official REST API for accessing YouTube data. We use it to get video metadata (title, duration, privacy status, thumbnails).

**Why we need it (why not just use yt-dlp for metadata too?):**
- `yt-dlp` *can* fetch metadata, but it does so by scraping YouTube's web page, which is slow and fragile.
- The YouTube Data API is fast, reliable, and gives structured JSON responses.
- It lets us check if a video is private (returns `403`) or doesn't exist (returns `404`) before we even attempt to download anything.

**How to get an API key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project (or select an existing one).
3. Navigate to **APIs & Services → Library**.
4. Search for "YouTube Data API v3" and click **Enable**.
5. Go to **APIs & Services → Credentials**.
6. Click **Create Credentials → API Key**.
7. Copy the key and paste it into your `.env` file as `YOUTUBE_API_KEY=your_key_here`.

---

## 4.9 youtube-transcript-api (Caption Fetcher)

**What it is:** A Python library that fetches subtitles/captions from YouTube videos without needing an API key.

**Why we use it:**
If a video has captions (either manually uploaded by the creator or auto-generated by YouTube), we can grab the text directly — this is much faster than downloading audio and running speech-to-text. It takes <1 second instead of 10-30 seconds.

**Important 2026 API change (v1.x):**
The library underwent a major API overhaul in v1.x. Both the old static methods AND the intermediate instance methods were replaced:
```python
# OLD (broken): Static method pattern
YouTubeTranscriptApi.get_transcript(video_id)

# OLD (broken): Instance method with get_transcript
ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.get_transcript(video_id, languages=["en"])
```
The correct v1.x pattern:
```python
# CURRENT (v1.2.4+): Instance method with fetch()
ytt_api = YouTubeTranscriptApi()
transcript = ytt_api.fetch(video_id, languages=["en"])
# Returns a FetchedTranscript object with .snippets (not a list of dicts)
text = " ".join([snippet.text for snippet in transcript.snippets])
```

**Key v1.x API changes:**
| Old API | New API (v1.x) |
|---|---|
| `ytt_api.get_transcript()` | `ytt_api.fetch()` |
| `ytt_api.list_transcripts()` | `ytt_api.list()` |
| Returns `list[dict]` with `item["text"]` | Returns `FetchedTranscript` with `snippet.text` |

---

## 4.10 boto3 (AWS SDK for Python)

**What it is:** The official Amazon Web Services (AWS) SDK for Python. We use it to interact with S3-compatible storage (MinIO locally, real S3 in production).

**Why boto3 for MinIO?**
MinIO is designed to be a drop-in replacement for AWS S3. It speaks the exact same protocol. So we use `boto3` (the standard S3 client) and just point it at `http://localhost:9000` instead of `https://s3.amazonaws.com`. When we move to production, we change the URL — zero code changes.

---

## 4.11 Pydantic (Data Validation)

**What it is:** A Python library for data validation using type annotations. FastAPI uses Pydantic under the hood.

**Why we use it:**
- **Request Validation:** When someone calls our API with `{"url": "..."}`, Pydantic ensures the `url` field exists and is a string. If it's missing, FastAPI automatically returns a `422 Validation Error`.
- **Response Validation:** We define exactly what our API returns (title, duration, etc.). If our code accidentally returns the wrong shape, Pydantic catches it.
- **Settings Management:** `pydantic-settings` reads `.env` files and converts environment variables into typed Python objects (strings, integers, booleans).

---

## 4.12 Docker (Containerisation)

See [Section 7](#7-docker--what-it-is-why-we-use-it-and-every-command-explained) for a full deep-dive.

---

# 5. Environment Variables — The `.env` File Explained

Environment variables are configuration values that live *outside* the code. This is important because:
- You never want to hardcode passwords or API keys in source code (if someone reads your code, they'd have your passwords).
- Different environments (development, staging, production) need different values.
- The `.env` file is added to `.gitignore` so it never gets committed to version control.

Here is every variable, what it does, and why:

```env
# YouTube API Key (required for metadata)
YOUTUBE_API_KEY=AIzaSyBoq6dUEBEC0P62u0xUYoH6JHZfBLCqc-Y
```
**What:** Your personal API key for the YouTube Data API v3.
**Why:** Without this, the metadata fetcher cannot call Google's servers. It would fall back to returning mock/fake data.
**Where it's used:** `app/services/metadata_fetcher.py` — passed to `build("youtube", "v3", developerKey=...)`.

```env
# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0
```
**What:** The connection string for Redis.
**Format:** `redis://hostname:port/database_number`.
**Why `localhost`:** In Phase A, Redis runs on your local machine via Docker.
**Why `/0`:** Redis has 16 databases (numbered 0-15). We use database 0 (the default).
**Where it's used:** `app/core/celery_app.py` — used as both `broker` and `backend` for Celery.

```env
# MinIO/S3 Storage
MINIO_ENDPOINT=localhost:9000
```
**What:** The hostname and port where MinIO is running.
**Why `localhost:9000`:** In Phase A, MinIO runs locally via Docker on port 9000.
**In Phase B:** This would change to the MinIO service hostname inside Docker (e.g., `minio:9000`).

```env
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
```
**What:** The username and password for MinIO (equivalent to AWS Access Key ID and Secret Access Key).
**Why `minioadmin`:** This is MinIO's default root credential for local development. In production, these would be strong, unique passwords.

```env
MINIO_SECURE=false
```
**What:** Whether to use HTTPS (`true`) or HTTP (`false`) when connecting to MinIO.
**Why `false`:** Locally, MinIO runs without SSL/TLS certificates. In production, this would be `true`.

```env
MINIO_BUCKET_NAME=video-synopsis-audio
```
**What:** The name of the S3 bucket where audio files are stored.
**Why this name:** Convention chosen by the team. All audio files for the video-synopsis project go here.

```env
MAX_VIDEO_DURATION_MINUTES=180
```
**What:** The maximum video length allowed (in minutes). Videos longer than 3 hours (180 minutes) are rejected.
**Why a limit:** Downloading and processing a 10-hour video would consume excessive storage and time. This is a business rule.

---

# 6. Dependencies — The `requirements.txt` Explained

Every Python project lists its dependencies in `requirements.txt`. Here is every package, what it does, and why:

```
fastapi>=0.100.0              # The web framework (our API server)
uvicorn[standard]>=0.23.0     # The ASGI server that runs FastAPI
pydantic-settings>=2.0.0     # Reads .env files into typed Python settings
google-api-python-client>=2.0.0  # Google's official SDK (for YouTube Data API)
youtube-transcript-api>=0.6.0    # Fetches YouTube captions without an API key
yt-dlp>=2023.0.0             # Downloads audio from YouTube
boto3>=1.28.0                # AWS SDK (talks to MinIO/S3)
celery[redis]>=5.3.0         # Background task queue with Redis support
redis>=5.0.0                 # Python Redis client (for direct Redis operations)
isodate>=0.6.0               # Parses ISO 8601 durations (e.g., "PT4M13S" → 253 seconds)
pytest>=7.4.0                # Testing framework
httpx>=0.25.0                # HTTP client used by FastAPI's TestClient
```

**What does `>=0.100.0` mean?**
It means "install version 0.100.0 or any newer version". This ensures we get bug fixes and security patches.

**What does `[standard]` in `uvicorn[standard]` mean?**
Square brackets specify "extras" — optional dependencies. `uvicorn[standard]` installs uvicorn along with performance extras like `httptools` and `watchfiles` (for auto-reload).

**What does `[redis]` in `celery[redis]` mean?**
Installs Celery along with the Redis transport backend. Without this extra, Celery wouldn't know how to talk to Redis.

---

# 7. Docker — What It Is, Why We Use It, and Every Command Explained

## What is Docker?

Docker is a tool that lets you run applications inside isolated "containers". A container is like a lightweight virtual machine — it has its own filesystem, network, and processes, but shares the host OS kernel (so it's much faster and lighter than a full VM).

## Why we use Docker in this project

We need Redis and MinIO to run our application. Without Docker, you would need to:
1. Download and install Redis for Windows (which is not officially supported — Redis is a Linux tool).
2. Download, install, and configure MinIO manually.
3. Deal with port conflicts, configuration files, and startup scripts.

With Docker, we describe exactly what we need in a YAML file, run one command, and everything starts automatically:

## The `docker-compose.dev.yml` File — Line by Line

```yaml
services:
```
This declares the start of our service definitions. Each "service" becomes one Docker container.

```yaml
  redis:
    image: redis:7-alpine
```
- `redis:` — We're naming this service "redis".
- `image: redis:7-alpine` — Use the official Redis image, version 7, built on Alpine Linux (a minimal Linux distribution, making the image very small ~5MB instead of ~100MB).

```yaml
    ports:
      - "6379:6379"
```
- Maps port 6379 on your local machine to port 6379 inside the container. This is why `redis://localhost:6379` works — your local port 6379 is forwarded into the container.
- Format: `"host_port:container_port"`.

```yaml
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
```
- Docker periodically runs `redis-cli ping` inside the container. If Redis responds with `PONG`, it's healthy.
- Checks every 5 seconds, times out after 3 seconds, retries 3 times before marking as unhealthy.

```yaml
  minio:
    image: minio/minio:latest
```
- `minio:` — We're naming this service "minio".
- `image: minio/minio:latest` — Use the latest official MinIO image.

```yaml
    ports:
      - "9000:9000"
      - "9001:9001"
```
- Port 9000: The S3 API (our Python code talks to this).
- Port 9001: The web admin console (you open this in your browser).

```yaml
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
```
- Sets the root username and password for MinIO. These must match what's in our `.env` file (`MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`).

```yaml
    command: server /data --console-address ":9001"
```
- Tells MinIO to start in server mode, store data in `/data` directory (inside the container), and serve the admin console on port 9001.

```yaml
    volumes:
      - minio_data:/data
```
- Creates a Docker volume called `minio_data` that persists data even when the container is stopped/restarted. Without this, uploaded audio files would disappear every time you restart MinIO.

```yaml
volumes:
  minio_data:
```
- Declares the named volume. Docker manages where it's stored on disk.

## Docker Commands We Used

### Starting the containers
```bash
docker-compose -f docker-compose.dev.yml up -d
```
- `docker-compose` — The Docker Compose CLI tool (manages multi-container applications).
- `-f docker-compose.dev.yml` — Specifies which compose file to use (we named ours `docker-compose.dev.yml` to distinguish it from M1's production `docker-compose.yml`).
- `up` — Create and start the containers.
- `-d` — Detached mode (run in the background so you get your terminal back).

**What this command does:**
1. Pulls the `redis:7-alpine` image from Docker Hub (if not already cached).
2. Pulls the `minio/minio:latest` image from Docker Hub (if not already cached).
3. Creates a Docker network so the containers can talk to each other.
4. Creates the `minio_data` volume.
5. Starts both containers.
6. Returns you to the terminal prompt.

**What you see after running it:**
```
[+] Running 3/3
 ✔ Network youtube-ingestion_default  Created
 ✔ Container youtube-ingestion-redis-1  Started
 ✔ Container youtube-ingestion-minio-1  Started
```

### Stopping the containers
```bash
docker-compose -f docker-compose.dev.yml down
```
- Stops and removes the containers and network. The `minio_data` volume is preserved (your uploaded files survive).

### Stopping and deleting everything (including data)
```bash
docker-compose -f docker-compose.dev.yml down -v
```
- The `-v` flag also deletes volumes. This wipes all uploaded audio files.

### Checking container status
```bash
docker-compose -f docker-compose.dev.yml ps
```
- Shows which containers are running, their ports, and health status.

---

# 8. Running Without Docker — Alternatives and Problems

## Can we run without Docker?

Yes, but it's painful. Here's how and why:

### Running Redis without Docker (on Windows)

**Problem:** Redis does not officially support Windows. The last Windows-compatible version was 3.x (ancient).

**Option 1: Memurai** — A Windows-compatible Redis alternative. Download from [memurai.com](https://www.memurai.com/). It's a drop-in replacement that speaks the Redis protocol.

**Option 2: WSL2 (Windows Subsystem for Linux)** — Install WSL2, then install Redis natively inside the Linux subsystem:
```bash
wsl
sudo apt update && sudo apt install redis-server
sudo service redis-server start
```
Then your `REDIS_URL=redis://localhost:6379/0` would still work because WSL2 shares the network with Windows.

**Option 3: Cloud Redis** — Use a free tier of [Redis Cloud](https://redis.com/try-free/) and change your `REDIS_URL` to point to the cloud instance.

### Running MinIO without Docker

**Option 1: MinIO standalone binary** — Download the MinIO binary for Windows from [min.io/download](https://min.io/download). Run it with:
```bash
minio.exe server D:\minio-data --console-address ":9001"
```
This stores files in `D:\minio-data` and runs the console on port 9001.

**Option 2: Use real AWS S3** — Create an AWS account, create an S3 bucket, and update your `.env`:
```env
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=your_aws_access_key
MINIO_SECRET_KEY=your_aws_secret_key
MINIO_SECURE=true
```
This works because our code uses `boto3` which natively supports AWS S3.

### Problems you face without Docker

1. **"Works on my machine" syndrome**: Docker guarantees that Redis 7 and MinIO run identically on every developer's machine. Without it, one person might have Redis 3.x, another has 7.x, and things break differently.
2. **Installation complexity**: You need to find, download, install, and configure each service manually. Docker does this in one command.
3. **Port conflicts**: If another application is already using port 6379 or 9000, you need to manually resolve conflicts.
4. **No health checks**: Docker automatically monitors service health. Without it, you'd need to manually verify each service is running.
5. **Cleanup difficulty**: Docker containers are disposable — `docker-compose down` and everything is gone. Without Docker, you need to uninstall each service manually.

---

# 9. Code Deep-Dive — Every File Explained Line by Line

## 9.1 `app/core/config.py` — Configuration Management

This file is the **single source of truth** for all application settings.

```python
from pydantic_settings import BaseSettings, SettingsConfigDict
```
- Imports `BaseSettings` from the `pydantic-settings` package. `BaseSettings` is a special class that automatically reads environment variables and `.env` files.
- `SettingsConfigDict` is the Pydantic v2 way of configuring settings behaviour.

```python
class Settings(BaseSettings):
    YOUTUBE_API_KEY: str = "YOUR_YOUTUBE_API_KEY"
    REDIS_URL: str = "redis://localhost:6379/0"
    
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_SECURE: bool = False
    MINIO_BUCKET_NAME: str = "video-synopsis-audio"
    
    MAX_VIDEO_DURATION_MINUTES: int = 180
```
- Each line defines a setting with a **type** and a **default value**.
- `YOUTUBE_API_KEY: str = "YOUR_YOUTUBE_API_KEY"` means: "This is a string. If no environment variable called `YOUTUBE_API_KEY` is found, use `YOUR_YOUTUBE_API_KEY` as the default."
- When the `.env` file exists, Pydantic reads the real value from it (e.g., your actual Google API key).

```python
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )
```
- `env_file=".env"` — Look for a file called `.env` in the current working directory.
- `env_file_encoding="utf-8"` — Read it as UTF-8 text.
- `extra="ignore"` — If the `.env` file contains variables that don't match any field in this class, silently ignore them (don't crash).

```python
settings = Settings()
```
- Creates a single global instance. Other files import this: `from app.core.config import settings`.
- At this moment, Pydantic reads the `.env` file and populates all the fields.

---

## 9.2 `app/core/celery_app.py` — Background Task System Setup

```python
from celery import Celery
from app.core.config import settings
```
- Imports the Celery class and our settings.

```python
celery_app = Celery(
    "worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.worker.tasks"]
)
```
- `"worker"` — A name for this Celery application (used in logs).
- `broker=settings.REDIS_URL` — **The message broker.** When FastAPI dispatches a task, the task message goes here. The Celery worker reads from here. Think of it as a "to-do list" stored in Redis.
- `backend=settings.REDIS_URL` — **The result backend.** When a task finishes, the result (success/failure + return value) is stored here. When you call `/status/{task_id}`, we read from here.
- `include=["app.worker.tasks"]` — Tells Celery where to find task definitions. Without this, Celery wouldn't know about `process_video_ingestion`.

```python
celery_app.conf.update(
    task_track_started=True,
    result_extended=True,
)
```
- `task_track_started=True` — **Critical.** Without this, Celery only reports `PENDING` and `SUCCESS/FAILURE`. With it, we also get `STARTED` and can set custom states like `FETCHING_METADATA` and `DOWNLOADING_AUDIO`. This is what makes the `/status` endpoint useful — the frontend can show a progress bar.
- `result_extended=True` — Store additional metadata with results (like execution time, worker name).

```python
celery_app.set_default()
```
- Sets this Celery instance as the default application. This is **critical** — without this line, `@shared_task` in `tasks.py` wouldn't know which Celery instance to bind to, and tasks would try to connect to the wrong broker (AMQP/RabbitMQ instead of Redis). **This was a bug we fixed during development.**

---

## 9.3 `app/main.py` — The FastAPI Web Server Entry Point

> [!IMPORTANT]
> **Phase A only.** In Phase B, M1 already has their own `main.py`. We just add our router to theirs.

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as video_router
from app.services.storage import ensure_bucket_exists
from app.core.config import settings
import uvicorn
```
- Imports FastAPI, CORS middleware, our routes, storage utility, settings, and uvicorn.

```python
app = FastAPI(title="YouTube Ingestion API")
```
- Creates the FastAPI application instance. The `title` appears in the Swagger UI documentation header.

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **CORS (Cross-Origin Resource Sharing)** middleware. Without this, a frontend running on `localhost:3000` would be blocked from calling our API on `localhost:8000`. Browsers enforce this security rule. `allow_origins=["*"]` means "allow requests from any origin" (fine for development, should be restricted in production).

```python
@app.on_event("startup")
def startup_event():
    ensure_bucket_exists(settings.MINIO_BUCKET_NAME)
```
- This function runs once when the server starts. It checks if the MinIO bucket `video-synopsis-audio` exists, and creates it if not. This way, we never get a "bucket not found" error during operation.

```python
@app.get("/health")
def health_check():
    return {"status": "ok"}
```
- A simple health check endpoint. Load balancers and monitoring tools hit this to verify the server is alive.

```python
app.include_router(video_router, prefix="/api/v1/videos", tags=["videos"])
```
- **This is the line that connects our routes to the server.** The `video_router` (from `routes.py`) contains 3 endpoints. With `prefix="/api/v1/videos"`, they become:
  - `POST /api/v1/videos/validate`
  - `POST /api/v1/videos/process`
  - `GET /api/v1/videos/status/{task_id}`
- `tags=["videos"]` groups them under "videos" in the Swagger UI.

```python
if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
```
- If you run `python -m app.main`, this starts uvicorn programmatically. Functionally identical to the `uvicorn app.main:app --reload --port 8000` terminal command.

---

## 9.4 `app/schemas/video.py` — Data Shape Definitions

```python
from pydantic import BaseModel
from typing import Optional, Any
```

```python
class VideoRequest(BaseModel):
    url: str
```
- **Input schema.** Every request to `/validate` and `/process` must include a JSON body with a `url` string. If the user sends `{}` (no url), FastAPI automatically returns `422 Validation Error`. We don't write this check ourselves — Pydantic handles it.

```python
class VideoMetadataResponse(BaseModel):
    title: str
    channel_name: str
    duration_seconds: int
    thumbnail_url: str
    has_captions: bool
```
- **Output schema for `/validate`.** Guarantees the response always contains these exact fields. Also shows up in Swagger UI so API consumers know exactly what to expect.

```python
class ProcessResponse(BaseModel):
    task_id: str
```
- **Output schema for `/process`.** Just returns the Celery task ID.

```python
class TaskStatusResponse(BaseModel):
    task_id: str
    state: str
    progress: Optional[str] = None
    result: Optional[Any] = None
```
- **Output schema for `/status`.** `Optional[str] = None` means the `progress` field may or may not be present (it's `None` when the task hasn't started yet).

---

## 9.5 `app/api/v1/routes.py` — The Three API Endpoints

### Endpoint 1: POST `/validate`

```python
@router.post("/validate", response_model=VideoMetadataResponse)
def validate_and_fetch_metadata(request: VideoRequest) -> Any:
    video_id = validate_url(request.url)
```
- `@router.post` — This function handles POST requests.
- `response_model=VideoMetadataResponse` — Tells FastAPI what the response looks like (for docs and validation).
- `request: VideoRequest` — FastAPI automatically parses the JSON body into a `VideoRequest` object.
- `validate_url(request.url)` — Extracts the 11-character YouTube Video ID or raises a 400 error.

```python
    try:
        metadata = get_video_metadata(video_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
```
- Calls the YouTube Data API. If it fails (video not found, private, too long), we catch the error and return it as a 400 Bad Request.

```python
    has_captions = False
    captions = None
    try:
        captions = fetch_captions(video_id)
        has_captions = bool(captions)
    except Exception:
        pass
    
    metadata["has_captions"] = has_captions
    metadata["captions_text"] = captions
    return metadata
```
- Tries to fetch captions from YouTube. If this fails for any reason, we silently set `has_captions = False`.
- `captions_text` contains the full transcript text (or `null` if none found). This lets the user preview the captions from the `/validate` endpoint without running a full processing task.

### Endpoint 2: POST `/process`

```python
@router.post("/process", response_model=ProcessResponse)
def start_processing(request: VideoRequest) -> Any:
    video_id = validate_url(request.url)
    task = process_video_ingestion.delay(request.url, video_id)
    return {"task_id": task.id}
```
- `.delay(...)` is Celery's way of saying "run this function in the background". It serializes the arguments, pushes a message to Redis, and returns immediately.
- `task.id` is a UUID string like `b8e9276e-efa4-4c70-8dd5-c9a67370d6ce`. The user uses this to check status.
- The actual processing happens in the Celery worker process — **not** in FastAPI.

### Endpoint 3: GET `/status/{task_id}`

```python
@router.get("/status/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> Any:
    task_result = AsyncResult(task_id, app=celery_app)
```
- `AsyncResult` queries Redis for the task's current state and result.
- `app=celery_app` tells it which Celery instance to use (so it connects to the right Redis).

```python
    return {
        "task_id": task_id,
        "state": task_result.state,
        "progress": task_result.info.get("progress") if isinstance(task_result.info, dict) else None,
        "result": task_result.result if task_result.state == "SUCCESS" else None
    }
```
- `task_result.state` — One of: `PENDING`, `STARTED`, `FETCHING_METADATA`, `FETCHING_CAPTIONS`, `UPLOADING_TRANSCRIPT`, `DOWNLOADING_AUDIO`, `CONVERTING_AUDIO`, `UPLOADING_AUDIO`, `COMPLETED`, `SUCCESS`, `FAILURE`.
- `task_result.info` — The `meta` dictionary from `self.update_state(...)` in the task.
- `task_result.result` — The final return value of the task (only available when state is `SUCCESS`). Contains `s3_transcript_uri` or `s3_audio_uri` depending on which path was taken.

> [!IMPORTANT]
> The result is checked against `"SUCCESS"` (Celery's built-in terminal state), not `"COMPLETED"`. `COMPLETED` is our custom state set just before `return`. Celery then automatically transitions to `SUCCESS`.

---

## 9.6 `app/services/url_validator.py` — YouTube URL Validation

```python
YOUTUBE_URL_PATTERN = re.compile(
    r'(?:https?:\/\/)?(?:www\.|m\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=|shorts\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)
```
This is a Regular Expression (RegEx) pattern. Let's break it down:

| Pattern Part | What It Matches |
|---|---|
| `(?:https?:\/\/)?` | Optional `http://` or `https://` |
| `(?:www\.\|m\.)?` | Optional `www.` or `m.` (mobile) |
| `youtube\.com\/` | The domain `youtube.com/` |
| `[?&]v=` | The `v=` parameter (e.g., `?v=ID` or `&v=ID`) |
| `shorts\/` | YouTube Shorts URLs (`/shorts/ID`) |
| `(?:v\|e(?:mbed)?)\/` | `/v/ID` or `/embed/ID` URLs |
| `youtu\.be\/` | Short URLs (`youtu.be/ID`) |
| `([a-zA-Z0-9_-]{11})` | **Captures exactly 11 characters** — the Video ID |

**URLs this regex handles:**
- `https://www.youtube.com/watch?v=dQw4w9WgXcQ`
- `https://youtu.be/dQw4w9WgXcQ`
- `https://youtube.com/embed/dQw4w9WgXcQ`
- `https://youtube.com/shorts/dQw4w9WgXcQ`
- `https://m.youtube.com/watch?v=dQw4w9WgXcQ`
- `https://youtu.be/FMOtyYU6pj8?si=Y7SltqTRLlz_8Anf` (with tracking params)

```python
def extract_video_id(url: str) -> Optional[str]:
    match = YOUTUBE_URL_PATTERN.search(url)
    if match:
        return match.group(1)
    return None
```
- `search(url)` scans the entire string for the pattern.
- `match.group(1)` returns the first captured group — the 11-character Video ID.
- Returns `None` if no match found.

```python
def validate_url(url: str) -> str:
    video_id = extract_video_id(url)
    if not video_id:
        raise HTTPException(status_code=400, detail="Invalid YouTube URL")
    return video_id
```
- Wraps `extract_video_id` with an HTTP error. If the URL is invalid, the API returns `400 Bad Request`.

---

## 9.7 `app/services/metadata_fetcher.py` — YouTube Metadata

```python
def get_video_metadata(video_id: str) -> dict:
    if settings.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY":
        return {
            "title": "Mock Video Title (Missing API Key)",
            ...
        }
```
- **Mock fallback.** If you haven't set a real API key, this returns fake data so the rest of the system can still be tested. This is a common pattern called a "stub" or "mock".

```python
    youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
```
- `build("youtube", "v3", ...)` creates a YouTube Data API v3 client using Google's official library. The `developerKey` is your API key.

```python
    request = youtube.videos().list(
        part="snippet,contentDetails,status",
        id=video_id
    )
    response = request.execute()
```
- Makes an HTTP GET request to `https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails,status&id={video_id}`.
- `snippet` — Contains title, channel name, description, thumbnails.
- `contentDetails` — Contains duration (in ISO 8601 format like `PT28M10S` = 28 minutes 10 seconds).
- `status` — Contains privacy status (public, private, unlisted).

```python
    duration_iso = content_details["duration"]
    duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
```
- YouTube returns duration in ISO 8601 format: `PT1H28M10S` means 1 hour, 28 minutes, 10 seconds.
- `isodate.parse_duration()` converts this to a Python `timedelta` object.
- `.total_seconds()` converts to a single number (e.g., `5290`).

---

## 9.8 `app/services/caption_fetcher.py` — Subtitle Extraction

```python
def fetch_captions(video_id: str) -> Optional[str]:
    try:
        ytt_api = YouTubeTranscriptApi()
```
- Creates a new instance of the transcript API. **Must be instantiated** — the old static method pattern was removed in the v1.x update.

```python
        try:
            transcript = ytt_api.fetch(video_id, languages=["en"])
        except (NoTranscriptFound, TranscriptsDisabled):
            transcript_list = ytt_api.list(video_id)
            first_transcript = next(iter(transcript_list))
            transcript = first_transcript.fetch()
```
- **First try:** `ytt_api.fetch()` gets English captions (`languages=["en"]`).
- **If no English captions exist:** Falls back to `ytt_api.list()` to get all available transcripts and takes the first one (could be Hindi, Spanish, auto-generated, etc.).
- `TranscriptsDisabled` — The video creator has explicitly disabled captions.
- `NoTranscriptFound` — No caption track exists in the requested language.

> [!IMPORTANT]
> The v1.x API renamed methods: `get_transcript()` → `fetch()`, `list_transcripts()` → `list()`. Using the old names silently fails because the broad `except Exception` catches the `AttributeError`.

```python
        if transcript and transcript.snippets:
            text = " ".join([snippet.text for snippet in transcript.snippets]).replace('\n', ' ')
            logger.info(f"Fetched {len(transcript.snippets)} caption segments for video {video_id}")
            return text
        return None
```
- In v1.x, `fetch()` returns a `FetchedTranscript` object (not a list of dicts).
- The transcript text is in `transcript.snippets` — each snippet has a `.text` attribute.
- We join all the `.text` values into a single string.
- Replace newlines with spaces for clean output.

```python
    except Exception as e:
        logger.warning(f"Caption fetch failed for video {video_id}: {type(e).__name__}: {e}")
        return None
```
- **Graceful failure with logging.** If anything goes wrong (network error, unknown exception), we log the warning and return `None`. This tells the caller "no captions available", which triggers the audio download fallback. We do NOT crash the pipeline.

---

## 9.9 `app/services/audio_pipeline.py` — Audio Download & Conversion

### `download_audio()`

```python
def download_audio(video_url: str, output_dir: str) -> str:
    output_template = os.path.join(output_dir, '%(id)s.%(ext)s')
```
- `%(id)s` and `%(ext)s` are yt-dlp template variables. They get replaced with the actual video ID and file extension. E.g., `C:\Users\...\scratch_FMOtyYU6pj8\FMOtyYU6pj8.m4a`.

```python
    ydl_opts = {
        'format': 'm4a/bestaudio/best',
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }
```
- `format: 'm4a/bestaudio/best'` — Download priority: try M4A first, then best audio format available, then best overall format. M4A is preferred because it's a common, efficient audio container.
- `quiet: True` — Suppress output (we don't need download progress bars in our logs).

```python
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(video_url, download=True)
```
- `extract_info(url, download=True)` — Extracts video information AND downloads the file. If `download=False`, it would only fetch metadata.
- Returns a dictionary with video info (title, ID, format, file path, etc.).

### `convert_to_wav()`

```python
def convert_to_wav(input_path: str, output_path: str) -> str:
    command = [
        'ffmpeg',
        '-i', input_path,   # Input file
        '-ac', '1',          # Audio channels: 1 (mono)
        '-ar', '16000',      # Audio sample rate: 16kHz
        '-y',                # Overwrite output without asking
        '-loglevel', 'error', # Only show errors
        output_path           # Output .wav file
    ]
    subprocess.run(command, check=True)
```
- `subprocess.run()` executes the FFmpeg command as a system process.
- `check=True` means Python will raise `CalledProcessError` if FFmpeg fails (e.g., corrupt input file, FFmpeg not installed).

### `cleanup_temp_files()`

```python
def cleanup_temp_files(paths: List[str]):
    for path in paths:
        if path and os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass
```
- Deletes intermediate files (the `.m4a` download and the `.wav` conversion) to prevent disk space leaks.
- Wrapped in try/except because the file might already be deleted or locked by another process.

---

## 9.10 `app/services/storage.py` — Cloud Storage (MinIO/S3)

```python
def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_SECURE else f"https://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name='us-east-1'
    )
```
- Creates a boto3 S3 client pointing at MinIO instead of AWS.
- `endpoint_url` is the key trick — it redirects the AWS SDK to MinIO's local address.
- `region_name='us-east-1'` — MinIO requires a region but doesn't actually use it. This is a placeholder.

```python
def ensure_bucket_exists(bucket_name: str):
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=bucket_name)
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 404:
            s3.create_bucket(Bucket=bucket_name)
        else:
            raise
```
- `head_bucket()` checks if a bucket exists (like pinging it).
- If it returns 404 (not found), we create it.
- If it returns another error (permissions, network), we let the error propagate.

```python
def upload_audio(file_path: str, video_id: str) -> str:
    ...
    object_name = f"audio/{video_id}.wav"
    s3.upload_file(file_path, bucket_name, object_name)
    return f"s3://{bucket_name}/{object_name}"
```
- Uploads the WAV audio file with the key `audio/FMOtyYU6pj8.wav` (like a file path inside the bucket).
- Returns a standard S3 URI: `s3://video-synopsis-audio/audio/FMOtyYU6pj8.wav`. Module 4 will use this URI to download the file and transcribe it.

```python
def upload_transcript(text: str, video_id: str) -> str:
    ...
    object_name = f"transcripts/{video_id}.txt"
    # Write text to a temp file, then upload
    tmp_path = os.path.join(tempfile.gettempdir(), f"{video_id}_transcript.txt")
    try:
        with open(tmp_path, 'w', encoding='utf-8') as f:
            f.write(text)
        s3.upload_file(tmp_path, bucket_name, object_name)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
    return f"s3://{bucket_name}/{object_name}"
```
- **This function stores YouTube caption text as a `.txt` file in S3/MinIO.**
- When captions exist, there is no audio to upload — we store the transcript text directly instead.
- Writes the text to a temporary file first because `boto3.upload_file()` requires a file path (not a string).
- The temp file is cleaned up in the `finally` block.
- Returns an S3 URI like: `s3://video-synopsis-audio/transcripts/dQw4w9WgXcQ.txt`.
- **This works identically in Phase A (MinIO) and Phase B (real S3)** — same function, same code, only the endpoint URL changes via `.env`.

---

## 9.11 `app/worker/tasks.py` — The Orchestrator (Celery Task)

This is the **most important file**. It ties everything together.

```python
@shared_task(bind=True, max_retries=3, acks_late=True)
def process_video_ingestion(self, video_url: str, video_id: str):
```
- `@shared_task` — Registers this function as a Celery task. When you call `.delay()`, Celery serializes the arguments and sends them to Redis.
- `bind=True` — Gives the function access to `self`, the task instance. We need `self` to call `self.update_state()` and `self.retry()`.
- `max_retries=3` — If the task fails, retry up to 3 times before giving up.
- `acks_late=True` — Don't acknowledge the message to Redis until the task is fully complete. If the worker crashes mid-task, Redis will re-deliver the message to another worker.

```python
    scratch_dir = os.path.join(tempfile.gettempdir(), f"scratch_{video_id}")
    os.makedirs(scratch_dir, exist_ok=True)
    temp_files = []
```
- Creates a temporary directory for this task's files. On Windows, `tempfile.gettempdir()` returns `C:\Users\<user>\AppData\Local\Temp`. We create `scratch_FMOtyYU6pj8` inside it.
- **Why not hardcode `/tmp/`?** Because `/tmp/` doesn't exist on Windows. Using `tempfile.gettempdir()` makes the code cross-platform.

```python
    try:
        # Step 1: Fetch metadata
        self.update_state(state='FETCHING_METADATA', meta={'progress': 'Fetching video metadata'})
        metadata = get_video_metadata(video_id)
```
- `self.update_state(...)` — Writes the custom state to Redis. When the user calls `/status/{task_id}`, they see `"state": "FETCHING_METADATA"` and `"progress": "Fetching video metadata"`. This is how the frontend shows progress to the user.

The task then branches based on whether captions are available:

```python
        if captions:
            # --- Captions found → store transcript text in S3 ---
            self.update_state(state='UPLOADING_TRANSCRIPT', meta={'progress': 'Uploading transcript to storage'})
            s3_transcript_uri = upload_transcript(captions, video_id)
        else:
            # --- No captions → download audio and store in S3 ---
            self.update_state(state='DOWNLOADING_AUDIO', meta={'progress': 'Downloading audio track'})
            audio_path = download_audio(video_url, scratch_dir)
            ...
            self.update_state(state='UPLOADING_AUDIO', meta={'progress': 'Uploading audio to storage'})
            s3_audio_uri = upload_audio(wav_path, video_id)
```

The task progresses through these states:

```mermaid
flowchart TD
    A["FETCHING_METADATA\n(Get title, duration, etc.)"] --> B["FETCHING_CAPTIONS\n(Try to get subtitles)"]
    B --> C{Captions found?}
    C -->|Yes| T["UPLOADING_TRANSCRIPT\n(Store .txt in S3/MinIO)"]
    T --> G["COMPLETED\n(Processing complete)"]
    C -->|No| D["DOWNLOADING_AUDIO\n(yt-dlp downloads audio)"]
    D --> E["CONVERTING_AUDIO\n(FFmpeg → 16kHz WAV)"]
    E --> F["UPLOADING_AUDIO\n(Upload .wav to S3/MinIO)"]
    F --> G
    G --> H["SUCCESS\n(Celery marks task done)"]
```

The result dict includes URIs for whichever path was taken:
```python
        result = {
            "video_id": video_id,
            "metadata": metadata,
            "has_captions": bool(captions),
            "s3_transcript_uri": s3_transcript_uri,  # Set when captions were found
            "s3_audio_uri": s3_audio_uri,              # Set when audio was downloaded
        }
```
- If captions exist: `s3_transcript_uri` = `s3://video-synopsis-audio/transcripts/dQw4w9WgXcQ.txt`, `s3_audio_uri` = `null`
- If no captions: `s3_transcript_uri` = `null`, `s3_audio_uri` = `s3://video-synopsis-audio/audio/FMOtyYU6pj8.wav`

```python
    except Exception as exc:
        logger.error(f"Task failed for {video_id}: {exc}")
        self.retry(exc=exc, countdown=30)
```
- If anything fails, log the error and retry after 30 seconds. This handles transient issues like network timeouts or YouTube rate limiting.

```python
    finally:
        cleanup_temp_files(temp_files)
        try:
            os.rmdir(scratch_dir)
        except OSError:
            pass
```
- The `finally` block **always runs**, even if the task fails. This ensures we clean up temporary files and don't leak disk space.

---

# 10. The Complete Data Flow — Visual Walkthrough

There are **two paths** depending on whether the video has captions. Here is the full flow for each:

## 10.1 Path A: Video HAS Captions (Transcript Stored)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant S as Swagger UI
    participant F as FastAPI Server<br/>(localhost:8000)
    participant V as url_validator.py
    participant R as Redis<br/>(localhost:6379)
    participant W as Celery Worker
    participant YT as YouTube APIs
    participant M as MinIO<br/>(localhost:9000)

    Note over U,M: Step 1: User submits URL via /process endpoint
    U->>S: Pastes YouTube URL
    S->>F: POST /api/v1/videos/process<br/>{"url": "https://youtu.be/..."}
    F->>V: validate_url(url)
    V-->>F: "dQw4w9WgXcQ" (Video ID)
    F->>R: Push task message to queue
    F-->>S: {"task_id": "13cd5d6f-..."}
    S-->>U: Shows task_id

    Note over W,M: Step 2: Celery worker picks up the task
    W->>R: Pop task from queue
    W->>YT: YouTube Data API v3<br/>get metadata
    YT-->>W: title, duration, thumbnail
    W->>YT: youtube-transcript-api<br/>fetch captions
    YT-->>W: Captions found! (2089 chars)

    Note over W,M: Step 3: Store transcript text in S3
    W->>M: Upload transcript as .txt file
    M-->>W: s3://video-synopsis-audio/transcripts/dQw4w9WgXcQ.txt

    Note over U,M: Step 4: User checks status
    U->>S: GET /status/13cd5d6f-...
    S->>F: GET /api/v1/videos/status/13cd5d6f-...
    F->>R: Lookup task result
    R-->>F: state=SUCCESS, result={has_captions: true, s3_transcript_uri: "s3://..."}
    F-->>S: {"state": "SUCCESS", "result": {...}}
    S-->>U: Shows result
```

## 10.2 Path B: Video has NO Captions (Audio Stored)

```mermaid
sequenceDiagram
    participant U as User (Browser)
    participant S as Swagger UI
    participant F as FastAPI Server<br/>(localhost:8000)
    participant V as url_validator.py
    participant R as Redis<br/>(localhost:6379)
    participant W as Celery Worker
    participant YT as YouTube APIs
    participant FF as FFmpeg
    participant M as MinIO<br/>(localhost:9000)

    Note over U,M: Step 1: User submits URL via /process endpoint
    U->>S: Pastes YouTube URL
    S->>F: POST /api/v1/videos/process<br/>{"url": "https://youtu.be/..."}
    F->>V: validate_url(url)
    V-->>F: "FMOtyYU6pj8" (Video ID)
    F->>R: Push task message to queue
    F-->>S: {"task_id": "b8e9276e-..."}
    S-->>U: Shows task_id

    Note over W,M: Step 2: Celery worker picks up the task
    W->>R: Pop task from queue
    W->>YT: YouTube Data API v3<br/>get metadata
    YT-->>W: title, duration, thumbnail
    W->>YT: youtube-transcript-api<br/>fetch captions
    YT-->>W: No captions available

    Note over W,M: Step 3: Fallback to audio download
    W->>YT: yt-dlp downloads audio
    YT-->>W: audio.m4a (26 MB)
    W->>FF: Convert to 16kHz mono WAV
    FF-->>W: audio.wav
    W->>M: Upload audio.wav
    M-->>W: s3://video-synopsis-audio/audio/FMOtyYU6pj8.wav

    Note over U,M: Step 4: User checks status
    U->>S: GET /status/b8e9276e-...
    S->>F: GET /api/v1/videos/status/b8e9276e-...
    F->>R: Lookup task result
    R-->>F: state=SUCCESS, result={has_captions: false, s3_audio_uri: "s3://..."}
    F-->>S: {"state": "SUCCESS", "result": {...}}
    S-->>U: Shows result
```

---

# 11. Phase A — Local Development and Testing

## What is Phase A?

Phase A is the "independent development" phase. We built and tested our module entirely on our local Windows machine, without needing any other team member's code.

## What is TEMPORARY in Phase A (not needed in Phase B)?

| File/Component | Purpose in Phase A | Why Not Needed in Phase B |
|---|---|---|
| `docker-compose.dev.yml` | Runs Redis + MinIO locally | M1's main `docker-compose.yml` already includes Redis + MinIO + Postgres + Nginx + everything |
| `app/main.py` | Our own mini FastAPI server | M1 already built the main FastAPI server. We just add our router to theirs |
| `venv/` | Local Python virtual environment | In production, Python runs inside a Docker container with its own environment |
| `.env` (the actual file) | Local secrets | M1's repo has its own `.env` with all secrets for all modules |
| `test_celery.py` | Debug script we created to test Celery connectivity | Only used during development debugging |

## What is PERMANENT in Phase A (also used in Phase B)?

| File/Component | Purpose | Carries Over to Phase B? |
|---|---|---|
| `app/services/url_validator.py` | URL validation logic | ✅ Yes — copied to `backend/app/services/` |
| `app/services/metadata_fetcher.py` | YouTube API integration | ✅ Yes — copied to `backend/app/services/` |
| `app/services/caption_fetcher.py` | Caption extraction | ✅ Yes — copied to `backend/app/services/` |
| `app/services/audio_pipeline.py` | Audio download + conversion | ✅ Yes — copied to `backend/app/services/` |
| `app/services/storage.py` | S3/MinIO upload | ✅ Yes — copied to `backend/app/services/` |
| `app/worker/tasks.py` | Celery task orchestration | ✅ Yes — copied to `backend/app/tasks/ingestion.py` |
| `app/api/v1/routes.py` | API endpoints | ✅ Yes — copied to `backend/app/api/videos.py` |
| `app/schemas/video.py` | Data models | ✅ Yes — copied to `backend/app/schemas/video.py` |

## How to Run Phase A (Step by Step)

1. **Start Docker Desktop** (make sure it's running).
2. **Start Redis + MinIO:**
   ```bash
   docker-compose -f docker-compose.dev.yml up -d
   ```
3. **Activate virtual environment:**
   ```bash
   .\venv\Scripts\activate
   ```
4. **Start FastAPI server (Terminal 1):**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```
5. **Start Celery worker (Terminal 2):**
   ```bash
   .\venv\Scripts\activate
   celery -A app.core.celery_app worker --loglevel=info --pool=solo
   ```
6. **Test at** `http://localhost:8000/docs`

## What We Tested and the Results

### Test 1: `/validate` endpoint (video WITH captions)
- **Input:** `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}`
- **Output:**
  ```json
  {
    "title": "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)",
    "channel_name": "Rick Astley",
    "duration_seconds": 214,
    "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    "has_captions": true,
    "captions_text": "♪ We're no strangers to love ♪ ♪ You know the rules and so do I ♪ ..."
  }
  ```
- **What happened:** URL validated → Metadata fetched → Captions found and extracted (2089 chars) → Response sent with full transcript text.

### Test 2: `/process` endpoint (video WITH captions — transcript stored)
- **Input:** `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}`
- **Output:** `{"task_id": "13cd5d6f-12d3-401c-aec1-d0530efaea30"}`
- **What happened in the Celery worker:** Captions found → transcript text uploaded to MinIO as `.txt`.

### Test 3: `/status/{task_id}` endpoint (captions path)
- **Input:** `13cd5d6f-12d3-401c-aec1-d0530efaea30`
- **Output:**
  ```json
  {
    "task_id": "13cd5d6f-...",
    "state": "SUCCESS",
    "progress": null,
    "result": {
      "video_id": "dQw4w9WgXcQ",
      "metadata": {"title": "Rick Astley - ...", ...},
      "has_captions": true,
      "s3_transcript_uri": "s3://video-synopsis-audio/transcripts/dQw4w9WgXcQ.txt",
      "s3_audio_uri": null
    }
  }
  ```

### Test 4: `/process` endpoint (video WITHOUT captions — audio stored)
- **Input:** A video URL where captions are disabled.
- **Output:** `{"task_id": "b8e9276e-..."}`
- **What happened in the Celery worker:**
  ```
  No captions for FMOtyYU6pj8. Falling back to audio download.
  [download] 100% of 26.08MiB in 00:00:04 at 5.83MiB/s
  Audio uploaded: s3://video-synopsis-audio/audio/FMOtyYU6pj8.wav
  ```

### Test 5: MinIO Console — Verify Both Paths
- Opened `http://localhost:9001`, logged in with `minioadmin/minioadmin`.
- Navigated to Object Browser → `video-synopsis-audio`.
- **`transcripts/` folder:** Contains `.txt` files (caption text for videos with captions).
- **`audio/` folder:** Contains `.wav` files (audio for videos without captions).

---

# 12. Phase B — Integration into the Complete Project

## What Changes?

### Files You COPY (Your Code → M1's Repo)

| Your File (Phase A) | Destination (Phase B) |
|---|---|
| `app/services/url_validator.py` | `backend/app/services/url_validator.py` |
| `app/services/metadata_fetcher.py` | `backend/app/services/metadata_fetcher.py` |
| `app/services/caption_fetcher.py` | `backend/app/services/caption_fetcher.py` |
| `app/services/audio_pipeline.py` | `backend/app/services/audio_pipeline.py` |
| `app/services/storage.py` | `backend/app/services/storage.py` |
| `app/worker/tasks.py` | `backend/app/tasks/ingestion.py` |
| `app/api/v1/routes.py` | `backend/app/api/videos.py` |
| `app/schemas/video.py` | `backend/app/schemas/video.py` |

### Files You DON'T COPY (Phase A Only)

| File | Why It's Not Copied |
|---|---|
| `docker-compose.dev.yml` | M1 has the full `docker-compose.yml` |
| `app/main.py` | M1 has their own main.py |
| `app/core/config.py` | M1 likely has their own settings class. You add your variables to it |
| `app/core/celery_app.py` | M1 already has Celery configured |
| `venv/` | Production uses Docker, not venv |
| `tests/` | You may choose to copy tests, but they may need import path adjustments |

### Dependencies You MERGE

Add these lines to M1's `backend/requirements.txt`:
```
google-api-python-client>=2.0.0
youtube-transcript-api>=0.6.0
yt-dlp>=2023.0.0
boto3>=1.28.0
isodate>=0.6.0
```
(Don't add `fastapi`, `celery`, `redis` etc. — M1 already has them.)

### Environment Variables You MERGE

Add these to M1's `.env` and `.env.example`:
```env
YOUTUBE_API_KEY=your_real_key
MAX_VIDEO_DURATION_MINUTES=180
```
(Don't add `REDIS_URL`, `MINIO_*` — M1 already has those configured.)

### The One Line to Connect Your Router

In M1's `main.py`, add:
```python
from app.api.videos import router as video_router
app.include_router(video_router, prefix="/api/v1/videos", tags=["videos"])
```

### How Module 4 Connects to You

In Phase A, our task logs the completed result:
```python
logger.info(f"Processing complete for {video_id}: {result}")
```

In Phase B, this becomes a real function call. Module 4 needs to handle **both** paths:
```python
from app.tasks.transcription import transcribe_audio  # Module 4's task

if captions:
    # Captions were found — transcript is already text, stored at s3_transcript_uri
    # M4 can skip speech-to-text and directly use the transcript
    process_transcript.delay(s3_transcript_uri, video_id, metadata)
else:
    # No captions — audio was downloaded, stored at s3_audio_uri
    # M4 needs to run speech-to-text (e.g., Whisper) on the audio
    transcribe_audio.delay(s3_audio_uri, video_id, metadata)
```

This triggers Module 4's Celery task, passing it:
- The S3 URI of either the **transcript text file** or the **audio file**.
- The video ID → so M4 knows which video this belongs to.
- The metadata → so M4 can store title/channel info alongside the transcript.

> [!IMPORTANT]
> **New in the current version:** `storage.py` now has **two upload functions**: `upload_audio()` (stores `.wav` files at `audio/{video_id}.wav`) and `upload_transcript()` (stores `.txt` files at `transcripts/{video_id}.txt`). Both are copied to Phase B.

### How `.env` Changes in Phase B

| Variable | Phase A Value | Phase B Value |
|---|---|---|
| `REDIS_URL` | `redis://localhost:6379/0` | `redis://redis:6379/0` (Docker service name) |
| `MINIO_ENDPOINT` | `localhost:9000` | `minio:9000` (Docker service name) |
| `MINIO_SECURE` | `false` | Could be `true` if using a real domain with SSL |

In Docker Compose, services refer to each other by their service name (e.g., `redis`, `minio`) instead of `localhost`, because each service runs in its own container with its own network.

```mermaid
flowchart TB
    subgraph "Phase A (Your Laptop)"
        LA[FastAPI<br/>localhost:8000]
        LR[Redis Container<br/>localhost:6379]
        LM[MinIO Container<br/>localhost:9000]
        LW[Celery Worker<br/>Your Terminal]
        LA --> LR
        LW --> LR
        LW --> LM
    end

    subgraph "Phase B (M1's Docker Network)"
        PA[FastAPI Container<br/>backend:8000]
        PR[Redis Container<br/>redis:6379]
        PM[MinIO Container<br/>minio:9000]
        PW[Celery Worker Container<br/>worker]
        PN[Nginx<br/>Port 80/443]
        PD[PostgreSQL<br/>postgres:5432]
        PA --> PR
        PW --> PR
        PW --> PM
        PN --> PA
        PA --> PD
    end
```

---

# 13. Testing — How We Verified Everything Works

## Automated Tests (pytest)

We ran `pytest tests/ -v` and all **9 tests passed**:

```
tests/test_api.py::test_validate_endpoint         PASSED  [11%]
tests/test_api.py::test_process_endpoint           PASSED  [22%]
tests/test_api.py::test_status_endpoint            PASSED  [33%]
tests/test_caption_fetcher.py::test_fetch_captions_success  PASSED  [44%]
tests/test_caption_fetcher.py::test_fetch_captions_disabled PASSED  [55%]
tests/test_metadata_fetcher.py::test_get_video_metadata_mock PASSED [66%]
tests/test_url_validator.py::test_extract_video_id PASSED  [77%]
tests/test_url_validator.py::test_validate_url_success     PASSED  [88%]
tests/test_url_validator.py::test_validate_url_failure     PASSED  [100%]
```

---

# 14. Errors We Encountered and How We Fixed Them

### Error 1: `500 Internal Server Error` on `/process` endpoint

**Symptom:** The `/validate` endpoint worked fine, but `/process` returned a `500` error.

**Root Cause:** When calling `process_video_ingestion.delay(...)`, Celery was trying to connect to AMQP/RabbitMQ (the default broker) instead of Redis. This happened because `@shared_task` wasn't properly bound to our Celery instance.

**Fix:** Added `celery_app.set_default()` in `celery_app.py` to make our Redis-configured Celery instance the default.

### Error 2: `docker-compose.dev.yml: the attribute version is obsolete`

**Symptom:** Warning when running `docker-compose up`.

**Root Cause:** Modern Docker Compose no longer requires the `version: '3.8'` field. It was removed as unnecessary.

**Fix:** Removed the `version: '3.8'` line from `docker-compose.dev.yml`.

### Error 3: `unable to get image 'minio/minio:latest'`

**Symptom:** Docker couldn't pull the MinIO image.

**Root Cause:** Docker Desktop was not running on the system.

**Fix:** Started Docker Desktop application before running `docker-compose up`.

### Error 4: Test `test_get_video_metadata_mock` failing

**Symptom:** Test expected mock data ("Mock Video Title...") but received real data ("Rick Astley - Never Gonna Give You Up...").

**Root Cause:** When a real YouTube API key was added to `.env`, the mock branch in `metadata_fetcher.py` was bypassed. The test was hardcoded to expect mock data.

**Fix:** Added `@patch('app.services.metadata_fetcher.settings.YOUTUBE_API_KEY', 'YOUR_YOUTUBE_API_KEY')` to force the test to always use the mock branch, regardless of what's in `.env`.

---

# 15. Glossary of Terms

| Term | Definition |
|---|---|
| **API** | Application Programming Interface — a set of URLs that applications use to communicate with each other |
| **API Key** | A secret string that identifies your application to a service (like a password for programs) |
| **ASGI** | Asynchronous Server Gateway Interface — the protocol FastAPI uses to communicate with the web server |
| **Broker** | A middleman that passes messages between producers (FastAPI) and consumers (Celery workers) |
| **Bucket** | A top-level folder in object storage (S3/MinIO) where files are stored |
| **Celery** | A Python library for running tasks in the background |
| **Container** | A lightweight, isolated runtime environment created by Docker |
| **CORS** | Cross-Origin Resource Sharing — a browser security mechanism that controls which websites can call your API |
| **Docker** | A platform for running applications inside containers |
| **Docker Compose** | A tool for defining and running multi-container Docker applications using a YAML file |
| **Endpoint** | A specific URL path that accepts HTTP requests (e.g., `/api/v1/videos/validate`) |
| **ENV file** | A file containing environment variables (key-value pairs) for configuration |
| **FastAPI** | A modern Python web framework for building APIs |
| **FFmpeg** | A multimedia framework for converting audio/video formats |
| **ISO 8601** | An international standard for representing dates, times, and durations (e.g., `PT1H28M10S`) |
| **MinIO** | An open-source object storage server compatible with Amazon S3 |
| **Mono** | Single audio channel (as opposed to stereo which has left + right) |
| **Object Storage** | A storage system that manages data as "objects" (files) in "buckets" (folders), accessible via HTTP |
| **Pydantic** | A Python library for data validation using type annotations |
| **Redis** | An in-memory key-value database used as a message broker and cache |
| **RegEx** | Regular Expression — a pattern-matching language for searching/validating text |
| **REST** | Representational State Transfer — an architectural style for designing web APIs |
| **S3** | Amazon Simple Storage Service — cloud object storage. MinIO is an S3-compatible alternative |
| **Sample Rate** | The number of audio samples captured per second. 16kHz = 16,000 samples/second |
| **Swagger UI** | An interactive API documentation page auto-generated by FastAPI at `/docs` |
| **UUID** | Universally Unique Identifier — a 128-bit random ID (e.g., `b8e9276e-efa4-4c70-8dd5-c9a67370d6ce`) |
| **Virtual Environment (venv)** | An isolated Python installation that keeps project dependencies separate from the system Python |
| **WAV** | An uncompressed audio file format used for high-quality audio processing |
| **Worker** | A background process that picks up and executes tasks from a queue |
| **YAML** | A human-readable data format used for configuration files (like `docker-compose.dev.yml`) |
| **yt-dlp** | A command-line tool and Python library for downloading video/audio from YouTube |

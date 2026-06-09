from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.routes import router as video_router
from app.services.storage import ensure_bucket_exists
from app.core.config import settings
import uvicorn

app = FastAPI(title="YouTube Ingestion API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    ensure_bucket_exists(settings.MINIO_BUCKET_NAME)

@app.get("/health")
def health_check():
    return {"status": "ok"}

app.include_router(video_router, prefix="/api/v1/videos", tags=["videos"])

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)

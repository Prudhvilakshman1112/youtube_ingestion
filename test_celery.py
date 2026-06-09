from app.core.celery_app import celery_app
from app.worker.tasks import process_video_ingestion
import traceback

try:
    task = process_video_ingestion.delay("https://youtu.be/FMOtyYU6pj8", "FMOtyYU6pj8")
    print("SUCCESS", task.id)
except Exception as e:
    print("ERROR:")
    traceback.print_exc()

import boto3
from botocore.exceptions import ClientError
from app.core.config import settings
import os

def get_s3_client():
    return boto3.client(
        's3',
        endpoint_url=f"http://{settings.MINIO_ENDPOINT}" if not settings.MINIO_SECURE else f"https://{settings.MINIO_ENDPOINT}",
        aws_access_key_id=settings.MINIO_ACCESS_KEY,
        aws_secret_access_key=settings.MINIO_SECRET_KEY,
        region_name='us-east-1' # Default for MinIO
    )

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

def upload_audio(file_path: str, video_id: str) -> str:
    s3 = get_s3_client()
    bucket_name = settings.MINIO_BUCKET_NAME
    object_name = f"audio/{video_id}.wav"
    
    s3.upload_file(file_path, bucket_name, object_name)
    
    # Return standard s3 URI format
    return f"s3://{bucket_name}/{object_name}"

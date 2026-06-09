from googleapiclient.discovery import build
from fastapi import HTTPException
import isodate
from app.core.config import settings

def get_video_metadata(video_id: str) -> dict:
    if settings.YOUTUBE_API_KEY == "YOUR_YOUTUBE_API_KEY":
        return {
            "title": "Mock Video Title (Missing API Key)",
            "channel_name": "Mock Channel",
            "duration_seconds": 60,
            "thumbnail_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
            "is_public": True
        }

    try:
        youtube = build("youtube", "v3", developerKey=settings.YOUTUBE_API_KEY)
        request = youtube.videos().list(
            part="snippet,contentDetails,status",
            id=video_id
        )
        response = request.execute()

        if not response.get("items"):
            raise HTTPException(status_code=404, detail="Video not found")

        item = response["items"][0]
        
        privacy_status = item["status"]["privacyStatus"]
        if privacy_status == "private":
            raise HTTPException(status_code=403, detail="Video is private")
            
        snippet = item["snippet"]
        content_details = item["contentDetails"]
        
        duration_iso = content_details["duration"]
        duration_seconds = int(isodate.parse_duration(duration_iso).total_seconds())
        
        if duration_seconds > (settings.MAX_VIDEO_DURATION_MINUTES * 60):
            raise HTTPException(
                status_code=400, 
                detail=f"Video exceeds maximum duration of {settings.MAX_VIDEO_DURATION_MINUTES} minutes"
            )

        return {
            "title": snippet["title"],
            "channel_name": snippet["channelTitle"],
            "duration_seconds": duration_seconds,
            "thumbnail_url": snippet["thumbnails"].get("high", snippet["thumbnails"].get("default"))["url"],
            "is_public": privacy_status == "public"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch metadata: {str(e)}")

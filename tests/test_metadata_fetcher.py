import pytest
from fastapi import HTTPException
from app.services.metadata_fetcher import get_video_metadata

# Note: These tests rely on the mock branch in metadata_fetcher.py 
# if the API key is not set.

from unittest.mock import patch

@patch('app.services.metadata_fetcher.settings.YOUTUBE_API_KEY', 'YOUR_YOUTUBE_API_KEY')
def test_get_video_metadata_mock():
    # Because YOUTUBE_API_KEY is not set (it defaults to YOUR_YOUTUBE_API_KEY in test environment)
    # this will hit the mock branch
    result = get_video_metadata("dQw4w9WgXcQ")
    
    assert "title" in result
    assert "channel_name" in result
    assert "duration_seconds" in result
    assert "thumbnail_url" in result
    assert "is_public" in result
    assert result["title"] == "Mock Video Title (Missing API Key)"

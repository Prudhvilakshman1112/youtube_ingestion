import pytest
from fastapi import HTTPException
from app.services.url_validator import extract_video_id, validate_url

def test_extract_video_id():
    assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://m.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert extract_video_id("https://www.youtube.com/shorts/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    assert extract_video_id("https://example.com") is None
    assert extract_video_id("not a url") is None

def test_validate_url_success():
    assert validate_url("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

def test_validate_url_failure():
    with pytest.raises(HTTPException) as excinfo:
        validate_url("https://example.com")
    assert excinfo.value.status_code == 400

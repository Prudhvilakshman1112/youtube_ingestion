import pytest
from unittest.mock import patch

def test_validate_endpoint(client):
    response = client.post(
        "/api/v1/videos/validate",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert "title" in data
    assert "duration_seconds" in data
    assert "has_captions" in data
    assert "captions_text" in data

@patch('app.api.v1.routes.process_video_ingestion')
def test_process_endpoint(mock_process, client):
    # Setup mock
    mock_task = mock_process.delay.return_value
    mock_task.id = "test-task-123"
    
    # Test
    response = client.post(
        "/api/v1/videos/process",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-123"
    mock_process.delay.assert_called_once_with("https://www.youtube.com/watch?v=dQw4w9WgXcQ", "dQw4w9WgXcQ")

@patch('app.api.v1.routes.AsyncResult')
def test_status_endpoint(mock_async_result, client):
    # Setup mock
    mock_task = mock_async_result.return_value
    mock_task.state = "FETCHING_METADATA"
    mock_task.info = {"progress": "Fetching video metadata"}
    mock_task.result = None
    
    # Test
    response = client.get("/api/v1/videos/status/test-task-123")
    assert response.status_code == 200
    data = response.json()
    assert data["task_id"] == "test-task-123"
    assert data["state"] == "FETCHING_METADATA"
    assert data["progress"] == "Fetching video metadata"

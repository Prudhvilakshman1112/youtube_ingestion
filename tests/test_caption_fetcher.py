import pytest
from unittest.mock import patch, MagicMock
from app.services.caption_fetcher import fetch_captions
from youtube_transcript_api import TranscriptsDisabled

@patch('app.services.caption_fetcher.YouTubeTranscriptApi')
def test_fetch_captions_success(mock_ytt_api):
    # Setup mock
    mock_transcript = [
        {"text": "Hello"},
        {"text": "World"}
    ]
    
    mock_instance = MagicMock()
    mock_instance.get_transcript.return_value = mock_transcript
    mock_ytt_api.return_value = mock_instance
    
    # Test
    result = fetch_captions("some_id")
    assert result == "Hello World"
    mock_instance.get_transcript.assert_called_once_with("some_id", languages=["en"])

@patch('app.services.caption_fetcher.YouTubeTranscriptApi')
def test_fetch_captions_disabled(mock_ytt_api):
    # Setup mock
    mock_instance = MagicMock()
    mock_instance.get_transcript.side_effect = TranscriptsDisabled("some_id")
    # list_transcripts should also fail if disabled
    mock_instance.list_transcripts.side_effect = TranscriptsDisabled("some_id")
    mock_ytt_api.return_value = mock_instance
    
    # Test
    result = fetch_captions("some_id")
    assert result is None

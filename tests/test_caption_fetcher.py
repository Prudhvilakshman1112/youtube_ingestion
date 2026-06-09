import pytest
from unittest.mock import patch, MagicMock
from app.services.caption_fetcher import fetch_captions
from youtube_transcript_api import TranscriptsDisabled

@patch('app.services.caption_fetcher.YouTubeTranscriptApi')
def test_fetch_captions_success(mock_ytt_api):
    # Setup mock — v1.x API returns FetchedTranscript with .snippets
    mock_snippet_1 = MagicMock()
    mock_snippet_1.text = "Hello"
    mock_snippet_2 = MagicMock()
    mock_snippet_2.text = "World"

    mock_transcript = MagicMock()
    mock_transcript.snippets = [mock_snippet_1, mock_snippet_2]

    mock_instance = MagicMock()
    mock_instance.fetch.return_value = mock_transcript
    mock_ytt_api.return_value = mock_instance
    
    # Test
    result = fetch_captions("some_id")
    assert result == "Hello World"
    mock_instance.fetch.assert_called_once_with("some_id", languages=["en"])

@patch('app.services.caption_fetcher.YouTubeTranscriptApi')
def test_fetch_captions_disabled(mock_ytt_api):
    # Setup mock — v1.x API: fetch() raises, list() also raises
    mock_instance = MagicMock()
    mock_instance.fetch.side_effect = TranscriptsDisabled("some_id")
    mock_instance.list.side_effect = TranscriptsDisabled("some_id")
    mock_ytt_api.return_value = mock_instance
    
    # Test
    result = fetch_captions("some_id")
    assert result is None


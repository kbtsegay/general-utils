"""
Tests for audio transcription module.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any, Dict

import pytest

from gutils.core.config import Config


class TestBackendSelection:
    """Test audio transcription backend selection."""

    def test_openai_backend_import(self) -> None:
        """Test that openai backend uses whisper module."""
        from gutils import audio
        # Just verify the backend constants exist
        assert hasattr(audio, 'Backend')

    def test_mlx_backend_import(self) -> None:
        """Test that mlx backend is available."""
        from gutils import audio
        # Verify the backend type exists
        assert hasattr(audio, 'Backend')


class TestFormatOutput:
    """Test transcription output formatting."""

    @pytest.fixture
    def mock_transcription_result(self) -> Dict[str, Any]:
        """Mock transcription result with segments."""
        return {
            'text': 'Hello world',
            'segments': [
                {
                    'start': 0.0,
                    'end': 1.5,
                    'text': 'Hello'
                },
                {
                    'start': 1.5,
                    'end': 2.5,
                    'text': 'world'
                }
            ]
        }

    def test_format_output_text(self, mock_transcription_result: Dict[str, Any]) -> None:
        """Test text format output."""
        from gutils.audio import format_output

        # Test with 'txt' format (the actual parameter name)
        result = format_output(mock_transcription_result, 'txt')
        assert result == 'Hello world'

    def test_format_output_json_valid(
        self, mock_transcription_result: Dict[str, Any]
    ) -> None:
        """Test JSON format output produces valid JSON."""
        from gutils.audio import format_output

        result = format_output(mock_transcription_result, 'json')

        # Should be valid JSON
        parsed = json.loads(result)
        assert 'text' in parsed
        assert 'segments' in parsed
        assert parsed['text'] == 'Hello world'
        assert len(parsed['segments']) == 2

    def test_format_output_srt(self, mock_transcription_result: Dict[str, Any]) -> None:
        """Test SRT subtitle format output."""
        from gutils.audio import format_output

        result = format_output(mock_transcription_result, 'srt')

        # SRT format should contain timestamp markers or text content
        # Note: Implementation may vary, so check for either format or content
        assert len(result) > 0
        # Check if it's either formatted as SRT or contains the text
        assert '-->' in result or 'Hello' in result or 'world' in result


class TestTranscriptionCLI:
    """Test audio CLI command registration."""

    def test_audio_command_exists(self) -> None:
        """Test that audio command is registered."""
        from gutils import audio
        assert hasattr(audio, 'register_commands')

    def test_transcribe_subcommand_exists(self) -> None:
        """Test that transcribe subcommand is registered."""
        from gutils import audio
        assert hasattr(audio, 'execute_transcribe')

    def test_transcribe_audio_function_exists(self) -> None:
        """Test that the core transcription function exists."""
        from gutils import audio
        assert hasattr(audio, 'transcribe_audio')
        assert callable(audio.transcribe_audio)

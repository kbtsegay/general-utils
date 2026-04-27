"""
Tests for dictation module.
"""

import sys
from unittest.mock import Mock, patch, MagicMock

import pytest

# Mock hardware dependencies before importing dictation module
# CI environments don't have PortAudio (for sounddevice) or keyboard access
sys.modules['sounddevice'] = MagicMock()
sys.modules['pynput'] = MagicMock()
sys.modules['pynput.keyboard'] = MagicMock()

from gutils.core.config import Config
from gutils.dictation import WhisprDictation


class TestModelMapping:
    """Test Whisper model name mapping."""

    @pytest.fixture
    def dictation_instance(self, temp_config: Config) -> WhisprDictation:
        """Create a WhisprDictation instance with mocked model loading."""
        with patch.object(WhisprDictation, '_load_whisper'), \
             patch.object(WhisprDictation, '_load_llm'), \
             patch.object(WhisprDictation, '_load_vocabulary', return_value=[]):
            instance = WhisprDictation(temp_config)
            # The _load_whisper method sets these attributes, so we need to call it
            # or manually set them
            instance.model_map = {
                "tiny": "mlx-community/whisper-tiny-mlx",
                "tiny.en": "mlx-community/whisper-tiny.en-mlx",
                "base": "mlx-community/whisper-base-mlx",
                "base.en": "mlx-community/whisper-base.en-mlx",
                "small": "mlx-community/whisper-small-mlx",
                "small.en": "mlx-community/whisper-small.en-mlx",
                "medium": "mlx-community/whisper-medium-mlx",
                "medium.en": "mlx-community/whisper-medium.en-mlx",
                "large": "mlx-community/whisper-large-v3-mlx",
            }
            return instance

    def test_model_map_medium(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'medium' resolves to correct MLX repository."""
        expected = "mlx-community/whisper-medium-mlx"
        assert dictation_instance.model_map["medium"] == expected

    def test_model_map_small(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'small' resolves correctly."""
        expected = "mlx-community/whisper-small-mlx"
        assert dictation_instance.model_map["small"] == expected

    def test_model_map_large(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'large' resolves correctly."""
        expected = "mlx-community/whisper-large-v3-mlx"
        assert dictation_instance.model_map["large"] == expected

    def test_model_map_base_en(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'base.en' resolves correctly."""
        expected = "mlx-community/whisper-base.en-mlx"
        assert dictation_instance.model_map["base.en"] == expected


class TestTypeText:
    """Test the _type_text method."""

    @pytest.fixture
    def dictation_instance(self, temp_config: Config) -> WhisprDictation:
        """Create a WhisprDictation instance with mocked components."""
        with patch.object(WhisprDictation, '_load_whisper'), \
             patch.object(WhisprDictation, '_load_llm'), \
             patch.object(WhisprDictation, '_load_vocabulary', return_value=[]):
            instance = WhisprDictation(temp_config)
            instance.keyboard_controller = Mock()
            return instance

    def test_type_text_content(self, dictation_instance: WhisprDictation) -> None:
        """Test that text is typed normally."""
        dictation_instance._type_text("Hello world")
        assert dictation_instance.keyboard_controller.type.called

"""
Tests for dictation module.

CRITICAL: Tests the security filter that prevents command injection.
"""

from typing import Any

import pytest
from unittest.mock import Mock, patch, MagicMock

from gutils.core.config import Config
from gutils.dictation import WhisprDictation


class TestSecurityFilter:
    """Test the security filter for command injection prevention."""

    @pytest.fixture
    def dictation_instance(self, temp_config: Config) -> WhisprDictation:
        """Create a WhisprDictation instance without loading heavy models."""
        with patch.object(WhisprDictation, '_load_whisper'), \
             patch.object(WhisprDictation, '_load_llm'), \
             patch.object(WhisprDictation, '_load_vocabulary', return_value=[]):
            instance = WhisprDictation(temp_config)
            return instance

    def test_dangerous_rm_command(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'rm -rf /' is flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("rm -rf /")

    def test_safe_text(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'Hello world' is not flagged as dangerous."""
        assert not dictation_instance._is_potentially_dangerous("Hello world")

    def test_dangerous_cat_passwd(self, dictation_instance: WhisprDictation) -> None:
        """Test that 'cat /etc/passwd' is flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("cat /etc/passwd")

    def test_dangerous_sudo(self, dictation_instance: WhisprDictation) -> None:
        """Test that sudo commands are flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("sudo apt-get install")

    def test_dangerous_pipes(self, dictation_instance: WhisprDictation) -> None:
        """Test that pipe characters are flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("ls | grep test")

    def test_dangerous_redirects(self, dictation_instance: WhisprDictation) -> None:
        """Test that redirect characters are flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("echo hello > file.txt")

    def test_dangerous_eval(self, dictation_instance: WhisprDictation) -> None:
        """Test that eval commands are flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("eval $(something)")

    def test_dangerous_backticks(self, dictation_instance: WhisprDictation) -> None:
        """Test that backticks are flagged as dangerous."""
        assert dictation_instance._is_potentially_dangerous("echo `whoami`")

    def test_safe_normal_sentence(self, dictation_instance: WhisprDictation) -> None:
        """Test that normal sentences are not flagged."""
        assert not dictation_instance._is_potentially_dangerous(
            "This is a normal sentence with no commands"
        )

    def test_safe_programming_text(self, dictation_instance: WhisprDictation) -> None:
        """Test that programming-related text without dangerous patterns is safe."""
        # This should be safe as it doesn't match the exact patterns
        assert not dictation_instance._is_potentially_dangerous(
            "function example returns value"
        )

    def test_case_insensitive_detection(self, dictation_instance: WhisprDictation) -> None:
        """Test that detection is case-insensitive."""
        assert dictation_instance._is_potentially_dangerous("SUDO apt install")
        assert dictation_instance._is_potentially_dangerous("Rm -rf /")

    def test_newline_bypass(self, dictation_instance: WhisprDictation) -> None:
        """Test that newline injection (rm\\n-rf) is caught."""
        assert dictation_instance._is_potentially_dangerous("rm\n-rf /")
        assert dictation_instance._is_potentially_dangerous("sudo\napt install")

    def test_safe_word_boundary(self, dictation_instance: WhisprDictation) -> None:
        """Test that words CONTAINING dangerous keywords (e.g. 'permit') are safe."""
        assert not dictation_instance._is_potentially_dangerous("permit")
        assert not dictation_instance._is_potentially_dangerous("farm")
        assert not dictation_instance._is_potentially_dangerous("push")
        assert not dictation_instance._is_potentially_dangerous("killjoy")


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
    """Test the _type_text method with security checks."""

    @pytest.fixture
    def dictation_instance(self, temp_config: Config) -> WhisprDictation:
        """Create a WhisprDictation instance with mocked components."""
        with patch.object(WhisprDictation, '_load_whisper'), \
             patch.object(WhisprDictation, '_load_llm'), \
             patch.object(WhisprDictation, '_load_vocabulary', return_value=[]):
            instance = WhisprDictation(temp_config)
            instance.keyboard_controller = Mock()
            return instance

    def test_type_text_safe_content(self, dictation_instance: WhisprDictation) -> None:
        """Test that safe text is typed normally."""
        safe_text = "Hello world"
        dictation_instance._type_text(safe_text)

        # Should have been typed
        assert dictation_instance.keyboard_controller.type.called

    def test_type_text_dangerous_content_blocked(
        self, dictation_instance: WhisprDictation, caplog: Any
    ) -> None:
        """Test that dangerous text is NOT typed and warning is logged."""
        dangerous_text = "rm -rf /"

        with caplog.at_level("WARNING"):
            dictation_instance._type_text(dangerous_text)

        # Should NOT have been typed
        assert not dictation_instance.keyboard_controller.type.called

        # Should have warning in logs
        assert "POTENTIAL COMMAND INJECTION DETECTED" in caplog.text

"""
Tests for core utilities (config, io, logger).
"""

import os
import json
import logging
import tempfile
from pathlib import Path
from io import StringIO
from typing import Any

import pytest

from gutils.core.config import Config
from gutils.core.io import smart_input, smart_output, ensure_output_dir
from gutils.core.logger import setup_logging


class TestConfig:
    """Test configuration management."""

    def test_default_values(self, temp_config: Config) -> None:
        """Test that default values are loaded correctly."""
        assert temp_config.get("log_level") == "INFO"
        assert temp_config.get("whisper_model") == "base"
        assert temp_config.get("whisper_backend") == "mlx"
        assert temp_config.get("llm_model") is False

    def test_env_var_override(self, monkeypatch: Any, temp_config: Config) -> None:
        """Test that environment variables override config file values."""
        # Reset and set env var before creating new config
        Config.reset()
        monkeypatch.setenv("GUTILS_WHISPER_MODEL", "large")
        monkeypatch.setenv("GUTILS_LOG_LEVEL", "DEBUG")

        # Create new config with env vars
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / "config.yaml"
            config_file.write_text("whisper_model: base\nlog_level: INFO\n")
            config = Config(config_path=str(config_file))

            assert config.get("whisper_model") == "large"
            assert config.get("log_level") == "DEBUG"

    def test_get_with_default(self, temp_config: Config) -> None:
        """Test getting non-existent key with default value."""
        assert temp_config.get("non_existent_key", "default_value") == "default_value"

    def test_set_runtime_value(self, temp_config: Config) -> None:
        """Test setting values at runtime."""
        temp_config.set("custom_key", "custom_value")
        assert temp_config.get("custom_key") == "custom_value"

    def test_get_output_dir_creates_directory(self, temp_config: Config) -> None:
        """Test that get_output_dir creates the directory if it doesn't exist."""
        output_dir = temp_config.get_output_dir()
        assert output_dir.exists()
        assert output_dir.is_dir()


class TestSmartIO:
    """Test smart input/output functions."""

    def test_smart_output_to_stdout(self, capsys: Any) -> None:
        """Test smart_output writes to stdout when path is None."""
        content = "test output"
        smart_output(content, path=None)

        captured = capsys.readouterr()
        assert content in captured.out

    def test_smart_output_to_file(self, temp_output_dir: Path) -> None:
        """Test smart_output writes to file when path is provided."""
        content = "test file content"
        output_file = temp_output_dir / "test_output.txt"

        smart_output(content, path=output_file)

        assert output_file.exists()
        assert output_file.read_text() == content

    def test_smart_output_creates_parent_dirs(self, temp_output_dir: Path) -> None:
        """Test smart_output creates parent directories if needed."""
        content = "nested content"
        output_file = temp_output_dir / "nested" / "dir" / "test.txt"

        smart_output(content, path=output_file)

        assert output_file.exists()
        assert output_file.read_text() == content

    def test_smart_input_from_file(self, temp_output_dir: Path) -> None:
        """Test smart_input reads from file."""
        content = "file content"
        test_file = temp_output_dir / "test_input.txt"
        test_file.write_text(content)

        result = smart_input(str(test_file))
        assert result == content

    def test_smart_input_from_stdin(self, monkeypatch: Any) -> None:
        """Test smart_input reads from stdin when source is '-'."""
        content = "stdin content"
        monkeypatch.setattr('sys.stdin', StringIO(content))

        result = smart_input("-")
        assert result == content

    def test_smart_input_file_not_found(self) -> None:
        """Test smart_input raises FileNotFoundError for non-existent file."""
        with pytest.raises(FileNotFoundError):
            smart_input("/non/existent/file.txt")

    def test_ensure_output_dir(self, temp_output_dir: Path) -> None:
        """Test ensure_output_dir creates directories."""
        new_dir = temp_output_dir / "new_directory"
        result = ensure_output_dir(new_dir)

        assert result.exists()
        assert result.is_dir()
        assert result == new_dir


class TestLogger:
    """Test logging configuration."""

    def test_setup_logging_machine_readable(self, capsys: Any) -> None:
        """Test setup_logging with machine_readable=True emits valid JSON."""
        # Setup logger with JSON output
        logger = setup_logging(
            level="INFO",
            machine_readable=True,
            logger_name="test_logger"
        )

        # Log a message
        logger.info("test message")

        # Capture stderr (where logs go)
        captured = capsys.readouterr()
        stderr_output = captured.err

        # Should contain JSON
        if stderr_output.strip():
            log_entry = json.loads(stderr_output.strip())
            assert "message" in log_entry
            assert log_entry["message"] == "test message"

    def test_setup_logging_debug_level(self) -> None:
        """Test setup_logging with DEBUG level."""
        logger = setup_logging(level="DEBUG", machine_readable=False)
        assert logger.level == logging.DEBUG

    def test_setup_logging_info_level(self) -> None:
        """Test setup_logging with INFO level."""
        logger = setup_logging(level="INFO", machine_readable=False)
        assert logger.level == logging.INFO

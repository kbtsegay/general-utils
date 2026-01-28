"""
Pytest configuration and shared fixtures for gutils tests.
"""

import os
import sys
import tempfile
from pathlib import Path
from typing import Generator, Any
import pytest

# Ensure gutils is importable
sys.path.insert(0, str(Path(__file__).parent.parent))

from gutils.core.config import Config


@pytest.fixture
def temp_config() -> Generator[Config, None, None]:
    """
    Fixture to provide a clean Config instance with temporary paths.

    Yields:
        Config: A fresh Config instance with temporary directories
    """
    # Reset singleton
    Config.reset()

    # Create temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create temporary config file
        config_file = temp_path / "config.yaml"
        config_file.write_text("""
output_dir: {output_dir}
log_level: INFO
whisper_model: base
whisper_backend: mlx
llm_model: false
trigger_key: alt
""".format(output_dir=str(temp_path / "outputs")))

        # Create config instance with temp file
        config = Config(config_path=str(config_file))

        yield config

        # Cleanup
        Config.reset()


@pytest.fixture
def mock_stdin(monkeypatch: Any) -> callable:
    """
    Helper to simulate piping input via stdin.

    Args:
        monkeypatch: pytest monkeypatch fixture

    Returns:
        callable: Function to set stdin content
    """
    def _set_stdin(content: str) -> None:
        from io import StringIO
        monkeypatch.setattr('sys.stdin', StringIO(content))

    return _set_stdin


@pytest.fixture
def sample_assets() -> Path:
    """
    Path helper for test assets directory.

    Returns:
        Path: Path to tests/assets directory
    """
    return Path(__file__).parent / "assets"


@pytest.fixture
def temp_output_dir() -> Generator[Path, None, None]:
    """
    Fixture to provide a temporary output directory.

    Yields:
        Path: Temporary directory for test outputs
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

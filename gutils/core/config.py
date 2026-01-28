"""
Configuration management for gutils.

Provides a singleton Config class that loads settings from multiple sources:
1. Built-in defaults
2. User config file (~/.gutils/config.yaml)
3. Environment variables (GUTILS_*)

Environment variables take precedence over config file, which takes precedence over defaults.
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """
    Singleton configuration manager.

    Load order (highest to lowest priority):
    1. Environment variables (GUTILS_*)
    2. User config file (~/.gutils/config.yaml)
    3. Default values
    """

    _instance: Optional["Config"] = None
    _config: Dict[str, Any] = {}
    _loaded: bool = False

    # Default configuration
    _defaults: Dict[str, Any] = {
        "output_dir": "outputs",
        "log_level": "INFO",
        "whisper_model": "base",
        "whisper_backend": "mlx",
        "llm_model": False,
        "gemini_api_key": None,
        "openai_api_key": None,
        "download_dir": "outputs",
        "trigger_key": "alt",
        "vocab_file": str(Path.home() / ".gutils" / "vocab.txt"),
    }

    def __new__(cls, config_path: Optional[str] = None) -> "Config":
        """Ensure only one instance exists (singleton pattern)."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize configuration.

        Args:
            config_path: Optional path to config file. If not provided, uses ~/.gutils/config.yaml
        """
        if self._loaded:
            return

        # Start with defaults
        self._config = self._defaults.copy()

        # Load from config file
        if config_path is None:
            config_path = str(Path.home() / ".gutils" / "config.yaml")

        if os.path.exists(config_path):
            self._load_from_file(config_path)

        # Override with environment variables
        self._load_from_env()

        self._loaded = True

    def _load_from_file(self, config_path: str) -> None:
        """Load configuration from YAML file."""
        try:
            with open(config_path, "r") as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    self._config.update(file_config)
        except Exception as e:
            # Silently fail if config file can't be loaded
            pass

    def _load_from_env(self) -> None:
        """Load configuration from environment variables."""
        env_mappings = {
            "GUTILS_OUTPUT_DIR": "output_dir",
            "GUTILS_LOG_LEVEL": "log_level",
            "GUTILS_WHISPER_MODEL": "whisper_model",
            "GUTILS_WHISPER_BACKEND": "whisper_backend",
            "GUTILS_LLM_MODEL": "llm_model",
            "GUTILS_GEMINI_API_KEY": "gemini_api_key",
            "GUTILS_OPENAI_API_KEY": "openai_api_key",
            "GUTILS_DOWNLOAD_DIR": "download_dir",
            "GUTILS_TRIGGER_KEY": "trigger_key",
            "GUTILS_VOCAB_FILE": "vocab_file",
            # Also support non-prefixed versions for API keys
            "GEMINI_API_KEY": "gemini_api_key",
            "GOOGLE_API_KEY": "gemini_api_key",
            "OPENAI_API_KEY": "openai_api_key",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Don't override if already set by a higher priority GUTILS_ var
                if env_var.startswith("GUTILS_") or config_key not in self._config or self._config[config_key] is None:
                    self._config[config_key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value at runtime.

        Args:
            key: Configuration key
            value: Value to set
        """
        self._config[key] = value

    def get_output_dir(self) -> Path:
        """Get the configured output directory as a Path object."""
        output_dir = Path(self.get("output_dir", "outputs"))
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir

    @classmethod
    def reset(cls) -> None:
        """Reset the singleton instance (useful for testing)."""
        cls._instance = None
        cls._loaded = False

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
            # Warn the user if config file exists but can't be parsed
            import sys
            print(f"Warning: Could not load config file at {config_path}: {e}", file=sys.stderr)

    def _load_from_env(self) -> None:
        """Load configuration from environment variables with clear priority."""
        env_mappings = {
            "output_dir": ["GUTILS_OUTPUT_DIR"],
            "log_level": ["GUTILS_LOG_LEVEL"],
            "whisper_model": ["GUTILS_WHISPER_MODEL"],
            "whisper_backend": ["GUTILS_WHISPER_BACKEND"],
            "llm_model": ["GUTILS_LLM_MODEL"],
            "gemini_api_key": ["GUTILS_GEMINI_API_KEY", "GEMINI_API_KEY", "GOOGLE_API_KEY"],
            "openai_api_key": ["GUTILS_OPENAI_API_KEY", "OPENAI_API_KEY"],
            "trigger_key": ["GUTILS_TRIGGER_KEY"],
            "vocab_file": ["GUTILS_VOCAB_FILE"],
        }

        for config_key, env_vars in env_mappings.items():
            for env_var in env_vars:
                value = os.getenv(env_var)
                if value is not None:
                    self._config[config_key] = value
                    break  # First found environment variable takes priority

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

"""
Core utilities for gutils package.

This module provides shared functionality across all tools including:
- Logging configuration
- Configuration management
- I/O utilities
"""

from gutils.core.logger import setup_logging
from gutils.core.config import Config
from gutils.core.io import smart_input, smart_output

__all__ = ["setup_logging", "Config", "smart_input", "smart_output"]

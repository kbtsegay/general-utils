"""
I/O utilities for gutils.

Provides smart input/output functions that handle:
- Reading from stdin when argument is '-'
- Writing to stdout when no path is specified
- File reading/writing with proper error handling
"""

import sys
from pathlib import Path
from typing import Optional, Union


def smart_input(source: str) -> str:
    """
    Read input from file or stdin.

    If source is '-', reads from stdin.
    Otherwise, reads from the specified file path.

    Args:
        source: File path or '-' for stdin

    Returns:
        Content as string

    Raises:
        FileNotFoundError: If file doesn't exist
        IOError: If reading fails
    """
    if source == "-":
        # Read from stdin
        return sys.stdin.read()
    else:
        # Read from file
        file_path = Path(source)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {source}")

        try:
            return file_path.read_text()
        except Exception as e:
            raise IOError(f"Failed to read file {source}: {e}")


def smart_output(content: str, path: Optional[Union[str, Path]] = None) -> None:
    """
    Write output to file or stdout.

    If path is None, writes to stdout.
    Otherwise, writes to the specified file path.

    Args:
        content: Content to write
        path: File path or None for stdout

    Raises:
        IOError: If writing fails
    """
    if path is None:
        # Write to stdout
        sys.stdout.write(content)
        if not content.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
    else:
        # Write to file
        file_path = Path(path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            file_path.write_text(content)
        except Exception as e:
            raise IOError(f"Failed to write file {path}: {e}")


def ensure_output_dir(dir_path: Union[str, Path]) -> Path:
    """
    Ensure output directory exists.

    Args:
        dir_path: Directory path

    Returns:
        Path object for the directory
    """
    path = Path(dir_path)
    path.mkdir(parents=True, exist_ok=True)
    return path

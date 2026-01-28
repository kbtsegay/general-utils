"""
Main entry point for the gutils CLI.

Provides a unified command-line interface for all utility tools.
"""

import sys
import argparse
from typing import List, Optional

from gutils.core import setup_logging, Config


def create_parser() -> argparse.ArgumentParser:
    """
    Create the main argument parser with subparsers for each tool.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        prog="gutils",
        description="A unified CLI suite of powerful utility tools for macOS productivity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download YouTube video as MP3
  gutils tube download "https://youtube.com/watch?v=VIDEO_ID" --audio-only

  # Transcribe audio file
  gutils audio transcribe audio.mp3 --output-format json

  # Extract text from PDF
  gutils pdf extract document.pdf

  # Generate QR code
  gutils image qr "https://example.com" --style rounded

  # Generate AI image
  gutils image generate "A serene mountain landscape" --num-images 2

  # Start dictation daemon
  gutils dictation start

  # Composability example (pipe download to transcription)
  gutils tube download "https://..." --pipe | gutils audio transcribe - --json

For more help on a specific command:
  gutils <command> --help
  gutils <command> <subcommand> --help
        """,
    )

    # Global flags
    import gutils
    parser.add_argument(
        "--version",
        action="version",
        version=f"gutils {gutils.__version__}",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Force JSON output format (machine-readable)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    parser.add_argument(
        "--config",
        type=str,
        metavar="PATH",
        help="Path to custom config file (default: ~/.gutils/config.yaml)",
    )

    # Create subparsers for each module
    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True,
    )

    # Register module commands directly from the flattened modules
    import gutils.tube
    import gutils.audio
    import gutils.pdf
    import gutils.image
    import gutils.dictation

    gutils.tube.register_commands(subparsers)
    gutils.audio.register_commands(subparsers)
    gutils.pdf.register_commands(subparsers)
    gutils.image.register_commands(subparsers)
    gutils.dictation.register_commands(subparsers)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point for the gutils CLI.

    Args:
        argv: Command line arguments (defaults to sys.argv[1:])

    Returns:
        Exit code (0 for success, non-zero for error)
    """
    parser = create_parser()
    args = parser.parse_args(argv)

    # Initialize configuration
    config = Config(config_path=args.config)

    # Set up logging
    log_level = "DEBUG" if args.verbose else config.get("log_level", "INFO")
    machine_readable = args.json
    setup_logging(level=log_level, machine_readable=machine_readable)

    # Store global flags in config for access by subcommands
    config.set("json_output", args.json)
    config.set("verbose", args.verbose)

    try:
        # Execute the command (each module implements its own execute function)
        return args.func(args, config)
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        if args.verbose:
            import traceback
            traceback.print_exc()
        else:
            print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

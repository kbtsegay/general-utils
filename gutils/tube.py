"""
YouTube video/audio download tools.
"""

import sys
import logging
from argparse import ArgumentParser, _SubParsersAction
from pathlib import Path
from typing import Any, Optional, Dict

import yt_dlp

from gutils.core import Config

logger = logging.getLogger(__name__)


def register_commands(subparsers: _SubParsersAction) -> None:
    """
    Register tube subcommands.
    """
    tube_parser = subparsers.add_parser(
        "tube",
        help="YouTube video/audio download tools",
        description="Download videos or audio from YouTube",
    )

    tube_subparsers = tube_parser.add_subparsers(
        title="tube commands",
        description="Available tube operations",
        dest="tube_command",
        required=True,
    )

    # Download command
    download_parser = tube_subparsers.add_parser(
        "download",
        help="Download YouTube video or audio",
        description="Download a YouTube video or extract audio to MP3",
    )

    download_parser.add_argument(
        "url",
        type=str,
        help="YouTube video URL",
    )

    download_parser.add_argument(
        "--video",
        action="store_true",
        help="Download video instead of audio-only (default)",
    )

    download_parser.add_argument(
        "-o", "--output",
        type=str,
        metavar="DIR",
        help="Output directory (default: from config)",
    )

    download_parser.add_argument(
        "--pipe",
        action="store_true",
        help="Output only the filename to stdout for piping to other commands",
    )

    download_parser.set_defaults(func=execute_download)


def execute_download(args: Any, config: Config) -> int:
    """
    Execute the download command.
    """
    try:
        # Determine if audio-only or video
        audio_only = not args.video

        # Get output directory
        output_dir = Path(args.output) if args.output else None

        # Download
        quiet = args.pipe  # Suppress output if piping
        file_path = download_video(
            url=args.url,
            output_dir=output_dir,
            audio_only=audio_only,
            quiet=quiet,
        )

        # Output handling
        if args.pipe:
            # Only output the filename to stdout for piping
            print(file_path)
        else:
            # Human-readable output
            media_type = "Audio" if audio_only else "Video"
            logger.info(f"{media_type} saved to: {file_path}")

        return 0

    except Exception as e:
        logger.error(f"Download failed: {e}")
        return 1


def download_video(
    url: str,
    output_dir: Optional[Path] = None,
    audio_only: bool = True,
    quiet: bool = False,
) -> str:
    """
    Download a YouTube video or extract audio.
    """
    if not url or not url.strip():
        raise ValueError("URL cannot be empty")

    # Get output directory from config if not specified
    if output_dir is None:
        config = Config()
        output_dir = config.get_output_dir()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Track the downloaded file path
    downloaded_file: Optional[str] = None

    def progress_hook(d: Dict[str, Any]) -> None:
        """Hook to capture the downloaded file path."""
        nonlocal downloaded_file
        if d['status'] == 'finished':
            downloaded_file = d['filename']

    # Configure yt-dlp options
    ydl_opts: Dict[str, Any] = {
        'outtmpl': str(output_dir / '%(title)s.%(ext)s'),
        'quiet': quiet,
        'no_warnings': quiet,
        'progress_hooks': [progress_hook],
    }

    if audio_only:
        ydl_opts['format'] = 'bestaudio/best'
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        ydl_opts['format'] = 'bestvideo+bestaudio/best'

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading from: {url}")
            ydl.download([url])

            # If audio extraction was done, update the file extension
            if audio_only and downloaded_file:
                # yt-dlp returns the pre-conversion filename, update to .mp3
                downloaded_file = str(Path(downloaded_file).with_suffix('.mp3'))

            if not downloaded_file:
                raise RuntimeError("Download completed but file path not captured")

            logger.info(f"Successfully downloaded: {downloaded_file}")
            return downloaded_file

    except Exception as e:
        logger.error(f"Download failed: {e}")
        raise RuntimeError(f"Failed to download video: {e}") from e

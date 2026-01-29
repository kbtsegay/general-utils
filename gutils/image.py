"""
Image generation tools (QR codes and AI images).
"""

import os
import logging
import io
from argparse import _SubParsersAction
from pathlib import Path
from typing import Any, Optional, List, Tuple

import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import (
    RoundedModuleDrawer,
    CircleModuleDrawer,
    SquareModuleDrawer,
)
from qrcode.image.styles.colormasks import SolidFillColorMask
from google import genai
from google.genai import types
from PIL import Image

from gutils.core import Config

logger = logging.getLogger(__name__)

# Color name to RGB mapping
COLOR_MAP = {
    "black": (0, 0, 0),
    "white": (255, 255, 255),
    "red": (255, 0, 0),
    "green": (0, 128, 0),
    "blue": (0, 0, 255),
    "yellow": (255, 255, 0),
    "cyan": (0, 255, 255),
    "magenta": (255, 0, 255),
    "gray": (128, 128, 128),
    "darkred": (139, 0, 0),
    "darkblue": (0, 0, 139),
    "darkgreen": (0, 100, 0),
    "orange": (255, 165, 0),
    "purple": (128, 0, 128),
}


def register_commands(subparsers: _SubParsersAction) -> None:
    """
    Register image subcommands.
    """
    image_parser = subparsers.add_parser(
        "image",
        help="Image generation tools",
        description="Generate QR codes and AI images",
    )

    image_subparsers = image_parser.add_subparsers(
        title="image commands",
        description="Available image operations",
        dest="image_command",
        required=True,
    )

    # QR code generation command
    qr_parser = image_subparsers.add_parser(
        "qr",
        help="Generate QR code from URL",
        description="Generate customizable QR codes from URLs",
    )

    qr_parser.add_argument(
        "url",
        type=str,
        help="URL to encode in QR code",
    )

    qr_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file path (default: outputs/qr_code.png)",
    )

    qr_parser.add_argument(
        "--size",
        type=int,
        default=10,
        help="Box size in pixels (default: 10)",
    )

    qr_parser.add_argument(
        "--border",
        type=int,
        default=4,
        help="Border size in boxes (default: 4)",
    )

    qr_parser.add_argument(
        "--style",
        type=str,
        choices=["square", "rounded", "circle"],
        default="square",
        help="QR code style (default: square)",
    )

    qr_parser.add_argument(
        "--fill-color",
        type=str,
        default="black",
        help="QR code color: color name or hex like #FF0000 (default: black)",
    )

    qr_parser.add_argument(
        "--back-color",
        type=str,
        default="white",
        help="Background color: color name or hex like #FFFFFF (default: white)",
    )

    qr_parser.add_argument(
        "--format",
        type=str,
        choices=["PNG", "JPEG", "BMP", "GIF"],
        default="PNG",
        help="Output image format (default: PNG)",
    )

    qr_parser.set_defaults(func=execute_qr)

    # AI image generation command
    generate_parser = image_subparsers.add_parser(
        "generate",
        help="Generate AI images",
        description="Generate AI-powered images using Google Gemini",
    )

    generate_parser.add_argument(
        "prompt",
        type=str,
        help="Text description of image to generate",
    )

    generate_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file path or directory (default: outputs/image_NNN.png)",
    )

    generate_parser.add_argument(
        "--num-images",
        type=int,
        default=1,
        choices=range(1, 5),
        metavar="1-4",
        help="Number of images to generate (default: 1)",
    )

    generate_parser.add_argument(
        "--model",
        type=str,
        choices=["gemini-2.5-flash-image", "gemini-3-pro-image-preview"],
        default="gemini-2.5-flash-image",
        help="Model to use (default: gemini-2.5-flash-image)",
    )

    generate_parser.add_argument(
        "--aspect-ratio",
        type=str,
        choices=["1:1", "3:4", "4:3", "16:9", "9:16", "4:5", "5:4", "3:2", "2:3", "21:9"],
        default="1:1",
        help="Image aspect ratio (default: 1:1)",
    )

    generate_parser.add_argument(
        "--format",
        type=str,
        choices=["PNG", "JPEG"],
        default="PNG",
        help="Output image format (default: PNG)",
    )

    generate_parser.set_defaults(func=execute_generate)


def execute_qr(args: Any, config: Config) -> int:
    """
    Execute the QR code generation command.
    """
    try:
        # Determine output path
        if args.output:
            output_path = Path(args.output)
        else:
            output_dir = config.get_output_dir()
            output_path = output_dir / "qr_code.png"

        # Generate QR code
        generate_qr_code(
            url=args.url,
            output_path=output_path,
            size=args.size,
            border=args.border,
            style=args.style,
            fill_color=args.fill_color,
            back_color=args.back_color,
            format=args.format,
        )

        logger.info("QR code generated successfully")
        logger.info(f"Output saved to: {output_path.resolve()}")

        return 0

    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        return 1


def execute_generate(args: Any, config: Config) -> int:
    """
    Execute the AI image generation command.
    """
    try:
        # Get API key from config
        api_key = config.get("gemini_api_key")
        if not api_key:
            # Also check environment for non-prefixed versions
            api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")

        if not api_key:
            logger.error(
                "GEMINI_API_KEY or GOOGLE_API_KEY not set. "
                "Get your API key from: https://aistudio.google.com/apikey"
            )
            return 1

        # Generate images
        logger.info(f'Generating {args.num_images} image(s) from prompt: "{args.prompt}"')

        images = generate_ai_images(
            api_key=api_key,
            prompt=args.prompt,
            num_images=args.num_images,
            aspect_ratio=args.aspect_ratio,
            model=args.model,
        )

        # Determine output path
        output_path = Path(args.output) if args.output else None

        # Save images
        saved_paths = save_images(images, output_path, args.format)

        # Success messages
        logger.info(f"Successfully generated {len(saved_paths)} image(s)")
        for path in saved_paths:
            logger.info(f"Saved to: {path.resolve()}")

        return 0

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        return 1


def parse_color(color_str: str) -> Tuple[int, int, int]:
    """
    Parse color string to RGB tuple.
    """
    color_lower = color_str.lower()
    if color_lower in COLOR_MAP:
        return COLOR_MAP[color_lower]

    # Try parsing as hex
    if color_str.startswith("#"):
        hex_str = color_str.lstrip("#")
        try:
            return tuple(int(hex_str[i : i + 2], 16) for i in (0, 2, 4))  # type: ignore
        except (ValueError, IndexError):
            raise ValueError(f"Invalid hex color: {color_str}")

    raise ValueError(
        f"Unknown color: {color_str}. " "Use color names like 'red', 'blue' or hex like '#FF0000'"
    )


def generate_qr_code(
    url: str,
    output_path: Path,
    size: int = 10,
    border: int = 4,
    style: str = "square",
    fill_color: str = "black",
    back_color: str = "white",
    format: str = "PNG",
) -> None:
    """
    Generate QR code from URL with customization options.
    """
    if not url.strip():
        raise ValueError("URL cannot be empty")

    logger.info(f"Generating QR code for: {url}")

    try:
        fill_rgb = parse_color(fill_color)
        back_rgb = parse_color(back_color)

        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=size,
            border=border,
        )
        qr.add_data(url)
        qr.make(fit=True)

        module_drawer_map = {
            "square": SquareModuleDrawer(),
            "rounded": RoundedModuleDrawer(),
            "circle": CircleModuleDrawer(),
        }
        module_drawer = module_drawer_map.get(style, SquareModuleDrawer())

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=module_drawer,
            color_mask=SolidFillColorMask(back_rgb, fill_rgb),
        )

        output_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(output_path, format=format)
        logger.info(f"QR code saved to: {output_path}")

    except Exception as e:
        logger.error(f"QR code generation failed: {e}")
        raise RuntimeError(f"Failed to generate QR code: {e}") from e


def validate_prompt(prompt: str) -> None:
    """
    Validate prompt meets API requirements.
    """
    if not prompt.strip():
        raise ValueError("Prompt cannot be empty")

    if len(prompt) > 2000:
        raise ValueError(
            f"Prompt too long ({len(prompt)} chars). " "Keep it under 2000 characters (~480 tokens)"
        )


def generate_ai_images(
    api_key: str,
    prompt: str,
    num_images: int = 1,
    aspect_ratio: str = "1:1",
    model: str = "gemini-2.5-flash-image",
) -> List[Image.Image]:
    """
    Generate images using Gemini API.
    """
    validate_prompt(prompt)
    logger.info(f"Generating {num_images} image(s) using {model}")

    try:
        client = genai.Client(api_key=api_key)
        images = []

        # Use batch generation if num_images > 1
        config = types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            candidate_count=num_images,
            image_config=types.ImageConfig(aspect_ratio=aspect_ratio),
        )
        response = client.models.generate_content(model=model, contents=prompt, config=config)
        for part in response.parts:
            if part.inline_data:
                img_bytes = part.inline_data.data
                images.append(Image.open(io.BytesIO(img_bytes)))

        if not images:
            raise RuntimeError("No images were generated in the response")

        logger.info(f"Successfully generated {len(images)} image(s)")
        return images

    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        raise RuntimeError(f"Failed to generate images: {e}") from e


def save_images(
    images: List[Image.Image],
    output_path: Optional[Path],
    format: str,
) -> List[Path]:
    """
    Save images to disk.
    """
    saved_paths = []
    for i, img in enumerate(images, start=1):
        if output_path and len(images) == 1:
            file_path = output_path
        else:
            if output_path:
                output_dir = output_path if output_path.is_dir() else output_path.parent
                base_name = output_path.stem if not output_path.is_dir() else "image"
            else:
                output_dir = Path("outputs")
                base_name = "image"

            output_dir.mkdir(parents=True, exist_ok=True)
            file_path = output_dir / f"{base_name}_{i:03d}.{format.lower()}"

        file_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(file_path, format=format)
        saved_paths.append(file_path)
        logger.info(f"Saved image to: {file_path}")

    return saved_paths

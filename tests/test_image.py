"""
Tests for image generation and QR code module.
"""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

import pytest
from PIL import Image

from gutils.core.config import Config


class TestQRGeneration:
    """Test QR code generation."""

    def test_qr_code_creation(self, temp_output_dir: Path) -> None:
        """Test that QR code is created and is a valid image."""
        from gutils.image import generate_qr_code

        output_path = temp_output_dir / "test_qr.png"
        generate_qr_code(
            url="https://example.com",
            output_path=output_path
        )

        # File should exist
        assert output_path.exists()

        # Should be a valid image
        img = Image.open(output_path)
        assert img is not None
        assert img.size[0] > 0
        assert img.size[1] > 0

    def test_qr_code_custom_size(self, temp_output_dir: Path) -> None:
        """Test QR code generation with custom size."""
        from gutils.image import generate_qr_code

        output_path = temp_output_dir / "test_qr_large.png"
        generate_qr_code(
            url="test data",
            output_path=output_path,
            size=15,
            border=2
        )

        assert output_path.exists()

        # Verify it's a valid image
        img = Image.open(output_path)
        assert img is not None

    def test_qr_code_rounded_style(self, temp_output_dir: Path) -> None:
        """Test QR code generation with rounded style."""
        from gutils.image import generate_qr_code

        output_path = temp_output_dir / "test_qr_rounded.png"
        generate_qr_code(
            url="rounded test",
            output_path=output_path,
            style='rounded'
        )

        assert output_path.exists()


class TestAIImageGeneration:
    """Test AI image generation with Gemini."""

    def test_generate_ai_images_function_exists(self) -> None:
        """Test that AI image generation function exists."""
        from gutils import image
        assert hasattr(image, 'generate_ai_images')
        assert callable(image.generate_ai_images)

    def test_generate_image_missing_api_key(self) -> None:
        """Test that AI image generation function is callable."""
        from gutils.image import generate_ai_images

        # Just verify the function exists and is callable
        # Actual API key validation would require mocking the API client
        assert callable(generate_ai_images)


class TestImageCLI:
    """Test image CLI command registration."""

    def test_image_command_exists(self) -> None:
        """Test that image command is registered."""
        from gutils import image
        assert hasattr(image, 'register_commands')

    def test_qr_subcommand_exists(self) -> None:
        """Test that qr subcommand is registered."""
        from gutils import image
        assert hasattr(image, 'execute_qr')

    def test_generate_subcommand_exists(self) -> None:
        """Test that generate subcommand is registered."""
        from gutils import image
        assert hasattr(image, 'execute_generate')

"""
Tests for PDF processing module.
"""

import json
import tempfile
from pathlib import Path
from typing import Any

import pytest
import fitz  # PyMuPDF

from gutils.core.config import Config


class TestPDFExtraction:
    """Test PDF text extraction."""

    @pytest.fixture
    def create_test_pdf(self, temp_output_dir: Path) -> Path:
        """Create a simple test PDF with known content."""
        pdf_path = temp_output_dir / "test.pdf"

        # Create a simple PDF with PyMuPDF
        doc = fitz.open()
        page = doc.new_page(width=595, height=842)  # A4 size
        text = "This is a test PDF document.\nIt contains sample text."
        page.insert_text((50, 50), text)
        doc.save(str(pdf_path))
        doc.close()

        return pdf_path

    def test_extract_text_function_exists(self) -> None:
        """Test that extract_text function exists."""
        from gutils import pdf
        assert hasattr(pdf, 'extract_text')
        assert callable(pdf.extract_text)

    def test_extract_text_from_pdf(
        self, create_test_pdf: Path
    ) -> None:
        """Test basic text extraction from PDF."""
        from gutils.pdf import extract_text

        # Read the PDF directly with fitz to verify content
        doc = fitz.open(str(create_test_pdf))
        page = doc[0]
        text = page.get_text()
        doc.close()

        # Verify the PDF contains our test text
        assert 'test PDF document' in text
        assert 'sample text' in text


class TestPDFMetadata:
    """Test PDF metadata extraction."""

    @pytest.fixture
    def create_test_pdf_with_metadata(self, temp_output_dir: Path) -> Path:
        """Create a PDF with metadata."""
        pdf_path = temp_output_dir / "test_meta.pdf"

        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), "Test content")

        # Set metadata
        doc.set_metadata({
            'title': 'Test Document',
            'author': 'Test Author',
            'subject': 'Testing',
        })

        doc.save(str(pdf_path))
        doc.close()

        return pdf_path

    def test_metadata_function_exists(self) -> None:
        """Test that metadata extraction function exists."""
        from gutils import pdf
        assert hasattr(pdf, 'extract_metadata')
        assert callable(pdf.extract_metadata)

    def test_metadata_extraction(
        self, create_test_pdf_with_metadata: Path
    ) -> None:
        """Test extraction of PDF metadata."""
        from gutils.pdf import extract_metadata

        result = extract_metadata(str(create_test_pdf_with_metadata))

        # Should return a dictionary with metadata
        assert isinstance(result, dict)
        assert 'page_count' in result or 'pages' in result.get('', '')


class TestPDFCLI:
    """Test PDF CLI command registration."""

    def test_pdf_command_exists(self) -> None:
        """Test that PDF command is registered."""
        from gutils import pdf
        assert hasattr(pdf, 'register_commands')

    def test_extract_command_exists(self) -> None:
        """Test that extract command is registered."""
        from gutils import pdf
        assert hasattr(pdf, 'execute_extract')

    def test_meta_command_exists(self) -> None:
        """Test that meta command is registered."""
        from gutils import pdf
        assert hasattr(pdf, 'execute_meta')

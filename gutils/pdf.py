"""
PDF text extraction tools using PyMuPDF and Tesseract OCR.
"""

import logging
import json
import io
from argparse import _SubParsersAction
from pathlib import Path
from typing import Any, Dict, Literal

import fitz  # PyMuPDF
from PIL import Image
import pytesseract

from gutils.core import Config, smart_output

logger = logging.getLogger(__name__)

ExtractionMethod = Literal["direct", "ocr"]


def register_commands(subparsers: _SubParsersAction) -> None:
    """
    Register PDF subcommands.
    """
    pdf_parser = subparsers.add_parser(
        "pdf",
        help="PDF text extraction tools",
        description="Extract text and metadata from PDF files",
    )

    pdf_subparsers = pdf_parser.add_subparsers(
        title="pdf commands",
        description="Available PDF operations",
        dest="pdf_command",
        required=True,
    )

    # Extract text command
    extract_parser = pdf_subparsers.add_parser(
        "extract",
        help="Extract text from PDF",
        description="Extract text from PDF files using direct parsing or OCR",
    )

    extract_parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to PDF file",
    )

    extract_parser.add_argument(
        "--method",
        type=str,
        choices=["direct", "ocr"],
        default="direct",
        help="Extraction method: 'direct' for native text, 'ocr' for scanned PDFs (default: direct)",
    )

    extract_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file path (default: stdout)",
    )

    extract_parser.add_argument(
        "--format",
        type=str,
        choices=["txt", "json"],
        default="txt",
        help="Output format (default: txt)",
    )

    extract_parser.add_argument(
        "--metadata",
        action="store_true",
        help="Include PDF metadata in output",
    )

    extract_parser.set_defaults(func=execute_extract)

    # Metadata command
    meta_parser = pdf_subparsers.add_parser(
        "meta",
        help="Extract PDF metadata",
        description="Extract metadata information from PDF files",
    )

    meta_parser.add_argument(
        "pdf_file",
        type=str,
        help="Path to PDF file",
    )

    meta_parser.add_argument(
        "-o",
        "--output",
        type=str,
        metavar="FILE",
        help="Output file path (default: stdout)",
    )

    meta_parser.set_defaults(func=execute_meta)


def execute_extract(args: Any, config: Config) -> int:
    """
    Execute the extract command.
    """
    try:
        # Extract text
        text = extract_text(
            pdf_path=args.pdf_file,
            method=args.method,
        )

        # Get metadata if requested
        metadata = None
        if args.metadata:
            metadata = extract_metadata(args.pdf_file)

        # Format output
        output_format = "json" if config.get("json_output") else args.format

        if output_format == "json":
            output_data = {
                "file_path": args.pdf_file,
                "text": text,
                "extraction_method": args.method,
            }
            if metadata:
                output_data["metadata"] = metadata

            output_text = json.dumps(output_data, indent=2, ensure_ascii=False)
        else:
            # Plain text format
            output_text = text
            if metadata:
                metadata_str = json.dumps(metadata, indent=2, ensure_ascii=False)
                output_text = f"METADATA:\n{metadata_str}\n\n{'-'*50}\nTEXT CONTENT:\n{text}"

        # Output handling
        if args.output:
            # Save to file
            output_path = Path(args.output)
            if output_format == "json":
                output_path = output_path.with_suffix(".json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding="utf-8")
            logger.info(f"Extracted text saved to: {output_path}")
        else:
            # Write to stdout
            smart_output(output_text)

        return 0

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        return 1


def execute_meta(args: Any, config: Config) -> int:
    """
    Execute the meta command.
    """
    try:
        # Extract metadata
        metadata = extract_metadata(args.pdf_file)

        # Format as JSON
        output_text = json.dumps(metadata, indent=2, ensure_ascii=False)

        # Output handling
        if args.output:
            # Save to file
            output_path = Path(args.output).with_suffix(".json")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output_text, encoding="utf-8")
            logger.info(f"Metadata saved to: {output_path}")
        else:
            # Write to stdout
            smart_output(output_text)

        return 0

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        return 1


def extract_text(
    pdf_path: str,
    method: ExtractionMethod = "direct",
) -> str:
    """
    Extract text from PDF file.
    """
    # Validate file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    if pdf_file.suffix.lower() != ".pdf":
        raise ValueError(f"File is not a PDF: {pdf_path}")

    logger.info(f"Extracting text from {pdf_path} using {method} method")

    try:
        if method == "ocr":
            text = _extract_text_with_ocr(pdf_path)
        else:
            text = _extract_text_direct(pdf_path)

            # Warn if very little text was extracted
            if len(text.strip()) < 100:
                logger.warning(
                    "Very little text extracted. This might be a scanned PDF. "
                    "Try using method='ocr' for better results."
                )

        logger.info(f"Extracted {len(text)} characters")
        return text

    except Exception as e:
        logger.error(f"Text extraction failed: {e}")
        raise RuntimeError(f"Failed to extract text: {e}") from e


def _extract_text_direct(pdf_path: str) -> str:
    """Extract text directly from PDF using PyMuPDF."""
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text += f"\n--- Page {page_num + 1} ---\n"
        text += page.get_text()

    doc.close()
    return text


def _extract_text_with_ocr(pdf_path: str) -> str:
    """Extract text from PDF using OCR on rendered images."""
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)

        # Render page as image with 2x scaling for better OCR
        mat = fitz.Matrix(2.0, 2.0)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        # Convert to PIL Image and run OCR
        image = Image.open(io.BytesIO(img_data))
        page_text = pytesseract.image_to_string(image)

        text += f"\n--- Page {page_num + 1} (OCR) ---\n"
        text += page_text

    doc.close()
    return text


def extract_metadata(pdf_path: str) -> Dict[str, Any]:
    """
    Extract metadata from PDF file.
    """
    # Validate file
    pdf_file = Path(pdf_path)
    if not pdf_file.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        doc = fitz.open(pdf_path)
        metadata = doc.metadata

        # Add page count
        metadata["page_count"] = len(doc)

        doc.close()
        return metadata

    except Exception as e:
        logger.error(f"Metadata extraction failed: {e}")
        raise RuntimeError(f"Failed to extract metadata: {e}") from e

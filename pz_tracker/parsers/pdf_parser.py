"""PDF parsing: text extraction and hyperlink discovery."""

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

import fitz  # PyMuPDF
import pdfplumber

from config import KEYWORDS

logger = logging.getLogger(__name__)


@dataclass
class AgendaItem:
    """A single relevant agenda item extracted from a PDF."""
    text: str
    page_number: int
    linked_urls: list[str] = field(default_factory=list)


# Pre-compile a single regex that matches any keyword (case-insensitive)
_KW_PATTERN = re.compile(
    "|".join(re.escape(kw) for kw in KEYWORDS),
    re.IGNORECASE,
)


def extract_text_pdfplumber(pdf_path: Path) -> list[tuple[int, str]]:
    """Return a list of (page_number, page_text) using pdfplumber."""
    pages: list[tuple[int, str]] = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for i, page in enumerate(pdf.pages, start=1):
                text = page.extract_text() or ""
                pages.append((i, text))
    except Exception:
        logger.exception("pdfplumber failed on %s", pdf_path)
    return pages


def extract_links_pymupdf(pdf_path: Path) -> dict[int, list[str]]:
    """Return {page_number: [url, …]} using PyMuPDF link extraction.

    Page numbers are 1-based to match pdfplumber output.
    """
    links_by_page: dict[int, list[str]] = {}
    try:
        doc = fitz.open(pdf_path)
        for page_idx in range(len(doc)):
            page = doc[page_idx]
            urls: list[str] = []
            for link in page.get_links():
                uri = link.get("uri")
                if uri:
                    urls.append(uri)
            if urls:
                links_by_page[page_idx + 1] = urls
            page = None  # release page resources
        doc.close()
    except Exception:
        logger.exception("PyMuPDF link extraction failed on %s", pdf_path)
    return links_by_page


def parse_agenda(pdf_path: Path) -> list[AgendaItem]:
    """Parse an agenda PDF and return relevant agenda items.

    Steps:
    1. Extract full text per page with pdfplumber.
    2. Split text into logical blocks (paragraphs / numbered items).
    3. Filter blocks that contain at least one keyword.
    4. Attach any hyperlinks from the same page (via PyMuPDF).
    """
    pages = extract_text_pdfplumber(pdf_path)
    links_by_page = extract_links_pymupdf(pdf_path)

    items: list[AgendaItem] = []
    for page_num, page_text in pages:
        # Split on double-newline or numbered-item patterns
        blocks = re.split(r"\n{2,}|\n(?=\d+[\.\)])", page_text)
        page_links = links_by_page.get(page_num, [])

        for block in blocks:
            block = block.strip()
            if not block:
                continue
            if _KW_PATTERN.search(block):
                items.append(
                    AgendaItem(
                        text=block,
                        page_number=page_num,
                        linked_urls=list(page_links),  # associate page-level links
                    )
                )

    logger.info(
        "Parsed %s: %d pages, %d relevant items found",
        pdf_path.name, len(pages), len(items),
    )
    return items


def extract_full_text(pdf_path: Path) -> str:
    """Return the full text of a PDF (all pages concatenated)."""
    pages = extract_text_pdfplumber(pdf_path)
    return "\n\n".join(text for _, text in pages)

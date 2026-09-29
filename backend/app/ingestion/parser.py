import re
from pathlib import Path
from typing import Dict, List

import pymupdf


# ---------------------------------------------------------
# Legal heading patterns
# ---------------------------------------------------------

PART_RE = re.compile(
    r"^(Part\s+[IVXLC]+)\s*[—\-:]\s*(.+)$",
    re.IGNORECASE,
)

CLAUSE_RE = re.compile(
    r"^Clause\s+\d+(?:\.\d+)*\.\s+\S.*$",
    re.IGNORECASE,
)

SECTION_RE = re.compile(
    r"^(Section\s+\d+(?:\.\d+)*)\.?\s*(.*)$",
    re.IGNORECASE,
)

ARTICLE_RE = re.compile(
    r"^(Article\s+\d+(?:\.\d+)*)\.?\s*(.*)$",
    re.IGNORECASE,
)

SCHEDULE_RE = re.compile(
    r"^(Schedule(?:\s+[A-Za-z0-9.]+)?)\s*[—\-:]\s*(.*)$",
    re.IGNORECASE,
)

ANNEXURE_RE = re.compile(
    r"^(Annexure(?:\s+[A-Za-z0-9.]+)?)\s*[—\-:]\s*(.*)$",
    re.IGNORECASE,
)

APPENDIX_RE = re.compile(
    r"^(Appendix(?:\s+[A-Za-z0-9.]+)?)\s*[—\-:]\s*(.*)$",
    re.IGNORECASE,
)


def classify_heading(text: str) -> Dict:
    """
    Identify legal headings.

    Returns:
        {
            "is_heading": bool,
            "heading_type": str,
            "heading_text": str
        }
    """

    text = text.strip()

    # Part
    match = PART_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "part",
            "heading_text": text,
        }

    # Clause
    match = CLAUSE_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "clause",
            "heading_text": text,
        }

    # Section
    match = SECTION_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "section",
            "heading_text": text,
        }

    # Article
    match = ARTICLE_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "article",
            "heading_text": text,
        }

    # Schedule
    match = SCHEDULE_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "schedule",
            "heading_text": text,
        }

    # Annexure
    match = ANNEXURE_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "annexure",
            "heading_text": text,
        }

    # Appendix
    match = APPENDIX_RE.match(text)

    if match:
        return {
            "is_heading": True,
            "heading_type": "appendix",
            "heading_text": text,
        }

    return {
        "is_heading": False,
        "heading_type": None,
        "heading_text": None,
    }


def parse_pdf(pdf_path: Path) -> List[Dict]:
    """
    Extract text from a PDF page by page.

    Output format:

    [
        {
            "page": 1,
            "lines": [
                {
                    "text": "...",
                    "is_heading": True/False,
                    "heading_type": "...",
                }
            ]
        }
    ]
    """

    pages = []

    document = pymupdf.open(pdf_path)

    try:

        for page_number, page in enumerate(document, start=1):

            raw_text = page.get_text("text")

            lines = []

            for raw_line in raw_text.splitlines():

                text = raw_line.strip()

                if not text:
                    continue

                heading_info = classify_heading(text)

                lines.append(
                    {
                        "text": text,
                        "is_heading": heading_info["is_heading"],
                        "heading_type": heading_info["heading_type"],
                        "heading_text": heading_info["heading_text"],
                    }
                )

            pages.append(
                {
                    "page": page_number,
                    "lines": lines,
                }
            )

    finally:
        document.close()

    return pages
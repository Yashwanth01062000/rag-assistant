import os
import re
from typing import Dict, List


# =========================================================
# METADATA MODE
# =========================================================

METADATA_MODE = os.getenv(
    "METADATA_MODE",
    "full_heading_path",
).strip().lower()

if METADATA_MODE not in {
    "full_heading_path",
    "page_only",
}:
    METADATA_MODE = "full_heading_path"


# =========================================================
# UTILITY FUNCTIONS
# =========================================================

def normalize_text(text: str) -> str:
    """
    Normalize whitespace while preserving readable text.
    """

    if not text:
        return ""

    text = text.replace("\r", "\n")

    text = re.sub(
        r"[ \t]+",
        " ",
        text,
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text,
    )

    return text.strip()


def token_like_count(text: str) -> int:
    """
    Lightweight token approximation.
    """

    if not text:
        return 0

    return len(
        re.findall(
            r"\S+",
            text,
        )
    )


# =========================================================
# TITLE NORMALIZATION
# =========================================================

def normalize_title(text: str) -> str:
    """
    Normalize document titles.

    Examples:

        COMMERCIAL SERVICES AGREEMENT
        commercial_services_agreement.pdf
        Commercial-Services-Agreement

    become equivalent.
    """

    if not text:
        return ""

    text = text.strip()

    # Remove PDF extension
    text = re.sub(
        r"\.pdf$",
        "",
        text,
        flags=re.IGNORECASE,
    )

    # Replace underscores and hyphens with spaces
    text = re.sub(
        r"[_\-]+",
        " ",
        text,
    )

    # Normalize whitespace
    text = re.sub(
        r"\s+",
        " ",
        text,
    )

    return text.strip().lower()


def is_document_title(
    text: str,
    document_title: str,
) -> bool:
    """
    Determine whether a line is the document title.

    Handles:

        COMMERCIAL SERVICES AGREEMENT
        commercial_services_agreement.pdf

    and similar filename/title variations.
    """

    text_normalized = normalize_title(text)
    title_normalized = normalize_title(document_title)

    # Direct normalized comparison
    if text_normalized == title_normalized:
        return True

    # Extra safety:
    # Compare individual words.
    text_words = text_normalized.split()
    title_words = title_normalized.split()

    if (
        text_words
        and title_words
        and text_words == title_words
    ):
        return True

    return False


# =========================================================
# DEVELOPMENT / TESTING NOTE
# =========================================================

def is_development_note(text: str) -> bool:
    """
    Detect the synthetic development/testing note
    used in the development PDFs.

    Example:

        Synthetic development/testing document —
        not a real contract.

    The slash in development/testing is normalized
    so it is correctly detected.
    """

    if not text:
        return False

    normalized = text.lower().strip()

    # Normalize separators:
    #
    # development/testing
    # development-testing
    # development_testing
    # development testing
    #
    # all become:
    #
    # development testing

    normalized = re.sub(
        r"[-_/]+",
        " ",
        normalized,
    )

    normalized = re.sub(
        r"\s+",
        " ",
        normalized,
    )

    return (
        "synthetic development testing document"
        in normalized
    )


# =========================================================
# METADATA FORMAT
# =========================================================

def format_metadata_path(unit: Dict) -> str:
    """
    Metadata experiment:

    full_heading_path:
        Part II — Fees and Payment > Clause 2. Fees

    page_only:
        Page 1
    """

    if METADATA_MODE == "full_heading_path":

        return (
            unit.get("heading_path")
            or "N/A"
        )

    if METADATA_MODE == "page_only":

        page_start = unit.get(
            "page_start"
        )

        page_end = unit.get(
            "page_end"
        )

        if page_start is None:
            return "Page N/A"

        if (
            page_end is None
            or page_end == page_start
        ):
            return f"Page {page_start}"

        return (
            f"Pages "
            f"{page_start}-{page_end}"
        )

    return (
        unit.get("heading_path")
        or "N/A"
    )


# =========================================================
# HEADING PATH
# =========================================================

def make_heading_path(
    document_title: str,
    current_part: str | None,
    current_clause: str | None,
    current_section: str | None,
    current_article: str | None,
    current_schedule: str | None,
) -> str:
    """
    Build hierarchical legal heading path.
    """

    parts = []

    if current_part:
        parts.append(
            current_part
        )

    if current_clause:
        parts.append(
            current_clause
        )

    elif current_section:
        parts.append(
            current_section
        )

    elif current_article:
        parts.append(
            current_article
        )

    elif current_schedule:
        parts.append(
            current_schedule
        )

    if parts:
        return " > ".join(parts)

    return document_title


# =========================================================
# EXTRACT LEGAL UNITS
# =========================================================

def extract_legal_units(
    pages: List[Dict],
    document_title: str,
) -> List[Dict]:
    """
    Convert parsed PDF lines into legal units.

    Expected parser structure:

        {
            "page": 1,
            "lines": [
                {
                    "text": "...",
                    "heading_type": "clause"
                }
            ]
        }

    Document titles and development notes are skipped.
    """

    units = []

    current_part = None
    current_clause = None
    current_section = None
    current_article = None
    current_schedule = None

    current_lines = []

    current_page_start = None
    current_page_end = None

    def flush_current():

        nonlocal current_lines
        nonlocal current_page_start
        nonlocal current_page_end

        if not current_lines:
            return

        text = normalize_text(
            "\n".join(
                line["text"]
                for line in current_lines
            )
        )

        if not text:

            current_lines = []
            current_page_start = None
            current_page_end = None

            return

        heading_path = make_heading_path(
            document_title=document_title,
            current_part=current_part,
            current_clause=current_clause,
            current_section=current_section,
            current_article=current_article,
            current_schedule=current_schedule,
        )

        units.append(
            {
                "text": text,

                "heading_path":
                    heading_path,

                "part":
                    current_part,

                "clause":
                    current_clause,

                "section":
                    current_section,

                "article":
                    current_article,

                "schedule":
                    current_schedule,

                "page_start":
                    current_page_start,

                "page_end":
                    current_page_end,
            }
        )

        current_lines = []

        current_page_start = None
        current_page_end = None

    # =====================================================
    # PROCESS EVERY PAGE
    # =====================================================

    for page in pages:

        page_number = page["page"]

        for line in page["lines"]:

            text = line["text"].strip()

            if not text:
                continue

            heading_type = line.get(
                "heading_type"
            )

            # =================================================
            # DOCUMENT TITLE
            # =================================================

            if (
                not current_part
                and not current_clause
                and not current_section
                and not current_article
                and not current_schedule
                and not current_lines
                and is_document_title(
                    text,
                    document_title,
                )
            ):
                continue

            # =================================================
            # DEVELOPMENT / TESTING NOTE
            # =================================================

            if (
                not current_part
                and not current_clause
                and not current_section
                and not current_article
                and not current_schedule
                and not current_lines
                and is_development_note(text)
            ):
                continue

            # =================================================
            # PART
            # =================================================

            if heading_type == "part":

                flush_current()

                current_part = text

                current_clause = None
                current_section = None
                current_article = None
                current_schedule = None

                continue

            # =================================================
            # CLAUSE
            # =================================================

            if heading_type == "clause":

                flush_current()

                current_clause = text

                current_section = None
                current_article = None
                current_schedule = None

                if current_page_start is None:
                    current_page_start = page_number

                current_page_end = page_number

                current_lines.append(
                    {
                        "text": text,
                        "page": page_number,
                    }
                )

                continue

            # =================================================
            # SECTION
            # =================================================

            if heading_type == "section":

                flush_current()

                current_section = text

                current_clause = None
                current_article = None
                current_schedule = None

                if current_page_start is None:
                    current_page_start = page_number

                current_page_end = page_number

                current_lines.append(
                    {
                        "text": text,
                        "page": page_number,
                    }
                )

                continue

            # =================================================
            # ARTICLE
            # =================================================

            if heading_type == "article":

                flush_current()

                current_article = text

                current_clause = None
                current_section = None
                current_schedule = None

                if current_page_start is None:
                    current_page_start = page_number

                current_page_end = page_number

                current_lines.append(
                    {
                        "text": text,
                        "page": page_number,
                    }
                )

                continue

            # =================================================
            # SCHEDULE / ANNEXURE / APPENDIX
            # =================================================

            if heading_type in {
                "schedule",
                "annexure",
                "appendix",
            }:

                flush_current()

                current_schedule = text

                current_clause = None
                current_section = None
                current_article = None

                if current_page_start is None:
                    current_page_start = page_number

                current_page_end = page_number

                current_lines.append(
                    {
                        "text": text,
                        "page": page_number,
                    }
                )

                continue

            # =================================================
            # NORMAL BODY TEXT
            # =================================================

            if current_page_start is None:
                current_page_start = page_number

            current_page_end = page_number

            current_lines.append(
                {
                    "text": text,
                    "page": page_number,
                }
            )

    # =====================================================
    # FLUSH FINAL UNIT
    # =====================================================

    flush_current()

    return units


# =========================================================
# CLAUSE-AWARE CHUNKING
# =========================================================

def clause_aware_chunks(
    pages: List[Dict],
    document_title: str,
    document_name: str,
    source_file: str,
    document_id: str,
    target_words: int = 450,
    overlap_percent: float = 0.0,
) -> List[Dict]:
    """
    Clause-aware chunking.

    Each legal clause becomes its own chunk unless
    the clause is larger than target_words.
    """

    units = extract_legal_units(
        pages=pages,
        document_title=document_title,
    )

    chunks = []

    chunk_number = 1

    for unit in units:

        text = unit["text"]

        if not text:
            continue

        words = text.split()

        # =================================================
        # NORMAL CLAUSE
        # =================================================

        if len(words) <= target_words:

            metadata_path = (
                format_metadata_path(
                    unit
                )
            )

            chunks.append(
                {
                    "chunk_id": (
                        f"{document_id}-"
                        f"clause-"
                        f"{chunk_number:04d}"
                    ),

                    "document_id":
                        document_id,

                    "document_name":
                        document_title,

                    "source_file":
                        source_file,

                    "document_type":
                        None,

                    "text":
                        text,

                    "heading_path":
                        metadata_path,

                    "part":
                        unit["part"],

                    "clause":
                        unit["clause"],

                    "section":
                        unit["section"],

                    "article":
                        unit["article"],

                    "schedule":
                        unit["schedule"],

                    "page_start":
                        unit["page_start"],

                    "page_end":
                        unit["page_end"],

                    "token_count":
                        token_like_count(
                            text
                        ),

                    "chunking_strategy":
                        "clause_aware",

                    "overlap_percent":
                        overlap_percent,

                    "metadata_mode":
                        METADATA_MODE,
                }
            )

            chunk_number += 1

            continue

        # =================================================
        # VERY LONG CLAUSE
        # =================================================

        overlap_words = int(
            target_words
            * overlap_percent
            / 100
        )

        if overlap_words >= target_words:
            overlap_words = 0

        start = 0

        while start < len(words):

            end = min(
                start + target_words,
                len(words),
            )

            piece_words = words[
                start:end
            ]

            piece_text = " ".join(
                piece_words
            )

            metadata_path = (
                format_metadata_path(
                    unit
                )
            )

            chunks.append(
                {
                    "chunk_id": (
                        f"{document_id}-"
                        f"clause-"
                        f"{chunk_number:04d}"
                    ),

                    "document_id":
                        document_id,

                    "document_name":
                        document_title,

                    "source_file":
                        source_file,

                    "document_type":
                        None,

                    "text":
                        piece_text,

                    "heading_path":
                        metadata_path,

                    "part":
                        unit["part"],

                    "clause":
                        unit["clause"],

                    "section":
                        unit["section"],

                    "article":
                        unit["article"],

                    "schedule":
                        unit["schedule"],

                    "page_start":
                        unit["page_start"],

                    "page_end":
                        unit["page_end"],

                    "token_count":
                        token_like_count(
                            piece_text
                        ),

                    "chunking_strategy":
                        "clause_aware",

                    "overlap_percent":
                        overlap_percent,

                    "metadata_mode":
                        METADATA_MODE,
                }
            )

            chunk_number += 1

            if end >= len(words):
                break

            start = end - overlap_words

    return chunks


# =========================================================
# FIXED 512-TOKEN CHUNKING
# =========================================================

def fixed_512_chunks(
    pages: List[Dict],
    document_title: str,
    document_name: str,
    source_file: str,
    document_id: str,
    fixed_tokens: int = 512,
    overlap_percent: float = 0.0,
) -> List[Dict]:
    """
    Fixed-size chunking.

    Supports:

        512 tokens + 0% overlap
        512 tokens + 15% overlap
    """

    all_words = []

    for page in pages:

        page_number = page["page"]

        for line in page["lines"]:

            text = line["text"].strip()

            if not text:
                continue

            # Skip document title
            if is_document_title(
                text,
                document_title,
            ):
                continue

            # Skip development note
            if is_development_note(text):
                continue

            for word in text.split():

                all_words.append(
                    {
                        "word": word,
                        "page": page_number,
                    }
                )

    if not all_words:
        return []

    overlap_tokens = int(
        fixed_tokens
        * overlap_percent
        / 100
    )

    if overlap_tokens >= fixed_tokens:
        overlap_tokens = 0

    chunks = []

    start = 0
    chunk_number = 1

    while start < len(all_words):

        end = min(
            start + fixed_tokens,
            len(all_words),
        )

        selected = all_words[
            start:end
        ]

        if not selected:
            break

        text = " ".join(
            item["word"]
            for item in selected
        )

        page_start = selected[0]["page"]
        page_end = selected[-1]["page"]

        if METADATA_MODE == "page_only":

            if page_start == page_end:

                metadata_path = (
                    f"Page {page_start}"
                )

            else:

                metadata_path = (
                    f"Pages "
                    f"{page_start}-"
                    f"{page_end}"
                )

        else:

            metadata_path = (
                f"Pages "
                f"{page_start}-"
                f"{page_end}"
            )

        chunks.append(
            {
                "chunk_id": (
                    f"{document_id}-"
                    f"fixed-"
                    f"{chunk_number:04d}"
                ),

                "document_id":
                    document_id,

                "document_name":
                    document_title,

                "source_file":
                    source_file,

                "document_type":
                    None,

                "text":
                    text,

                "heading_path":
                    metadata_path,

                "part":
                    None,

                "clause":
                    None,

                "section":
                    None,

                "article":
                    None,

                "schedule":
                    None,

                "page_start":
                    page_start,

                "page_end":
                    page_end,

                "token_count":
                    len(selected),

                "chunking_strategy":
                    "fixed_512",

                "overlap_percent":
                    overlap_percent,

                "metadata_mode":
                    METADATA_MODE,
            }
        )

        chunk_number += 1

        if end >= len(all_words):
            break

        start = end - overlap_tokens

    return chunks


# =========================================================
# CREATE CHUNKS
# =========================================================

def create_chunks(
    pages: List[Dict],
    document_title: str,
    document_name: str,
    source_file: str,
    document_id: str,
    strategy: str = "clause_aware",
    fixed_tokens: int = 512,
    overlap_percent: float = 0.0,
    target_words: int = 450,
) -> List[Dict]:

    strategy = (
        strategy
        .lower()
        .strip()
    )

    # =====================================================
    # CLAUSE-AWARE
    # =====================================================

    if strategy == "clause_aware":

        return clause_aware_chunks(
            pages=pages,

            document_title=document_title,

            document_name=document_name,

            source_file=source_file,

            document_id=document_id,

            target_words=target_words,

            overlap_percent=overlap_percent,
        )

    # =====================================================
    # FIXED 512
    # =====================================================

    if strategy in {
        "fixed",
        "fixed_512",
        "512",
        "fixed_512_tokens",
    }:

        return fixed_512_chunks(
            pages=pages,

            document_title=document_title,

            document_name=document_name,

            source_file=source_file,

            document_id=document_id,

            fixed_tokens=fixed_tokens,

            overlap_percent=overlap_percent,
        )

    raise ValueError(
        f"Unknown chunking strategy: "
        f"{strategy}. "
        f"Use 'clause_aware' or "
        f"'fixed_512'."
    )


# =========================================================
# BACKWARD-COMPATIBLE FUNCTION
# =========================================================

def chunk_document(
    pages: List[Dict],
    document_id: str,
    document_title: str,
    document_name: str = None,
    source_file: str = "",
    strategy: str = "clause_aware",
    fixed_tokens: int = 512,
    overlap_percent: float = 0.0,
    target_words: int = 450,
) -> List[Dict]:

    if document_name is None:
        document_name = document_title

    return create_chunks(
        pages=pages,

        document_title=document_title,

        document_name=document_name,

        source_file=source_file,

        document_id=document_id,

        strategy=strategy,

        fixed_tokens=fixed_tokens,

        overlap_percent=overlap_percent,

        target_words=target_words,
    )
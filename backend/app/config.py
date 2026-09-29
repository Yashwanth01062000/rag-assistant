from pathlib import Path
import os

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]

load_dotenv(BASE_DIR / "backend" / ".env", override=False)


# ---------------------------------------------------------
# Directories
# ---------------------------------------------------------

DATA_DIR = BASE_DIR / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
UPLOADS_DIR = DATA_DIR / "uploads"
DOCUMENTS_FILE = UPLOADS_DIR / "documents.json"

CHUNKS_FILE = DATA_DIR / "chunks" / "chunks.jsonl"
QDRANT_PATH = DATA_DIR / "qdrant"


# ---------------------------------------------------------
# Qdrant
# ---------------------------------------------------------

COLLECTION_NAME = os.getenv("QDRANT_COLLECTION", "legal_documents")


# ---------------------------------------------------------
# Embeddings / reranking
# ---------------------------------------------------------

EMBEDDING_MODEL = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-base-en-v1.5",
)

RERANKER_MODEL = os.getenv(
    "RERANKER_MODEL",
    "BAAI/bge-reranker-base",
)


# ---------------------------------------------------------
# Sarvam
# ---------------------------------------------------------

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_MODEL = os.getenv("SARVAM_MODEL", "sarvam-105b")


# ---------------------------------------------------------
# Chunking
# ---------------------------------------------------------

CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "clause_aware")
FIXED_CHUNK_TOKENS = int(os.getenv("FIXED_CHUNK_TOKENS", "512"))
CHUNK_OVERLAP_PERCENT = float(os.getenv("CHUNK_OVERLAP_PERCENT", "0"))
METADATA_MODE = os.getenv("METADATA_MODE", "full_heading_path")
CHUNK_TARGET_WORDS = int(os.getenv("CHUNK_TARGET_WORDS", "450"))
CHUNK_OVERLAP_WORDS = int(os.getenv("CHUNK_OVERLAP_WORDS", "80"))


# ---------------------------------------------------------
# Retrieval
# ---------------------------------------------------------

INITIAL_TOP_K = int(os.getenv("INITIAL_TOP_K", "6"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "3"))
SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.35"))
ENABLE_RERANKER = os.getenv("ENABLE_RERANKER", "false").lower() == "true"


# ---------------------------------------------------------
# Create required directories
# ---------------------------------------------------------

for directory in [
    PROCESSED_DIR,
    UPLOADS_DIR,
    CHUNKS_FILE.parent,
    QDRANT_PATH,
]:
    directory.mkdir(parents=True, exist_ok=True)

if not DOCUMENTS_FILE.exists():
    DOCUMENTS_FILE.write_text("[]", encoding="utf-8")

import json
import re
import time
import uuid
from pathlib import Path
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.config import (
    CHUNKING_STRATEGY,
    CHUNKS_FILE,
    CHUNK_OVERLAP_PERCENT,
    CHUNK_TARGET_WORDS,
    DOCUMENTS_FILE,
    FINAL_TOP_K,
    FIXED_CHUNK_TOKENS,
    INITIAL_TOP_K,
    SIMILARITY_THRESHOLD,
    UPLOADS_DIR,
    ENABLE_RERANKER,
)
from app.embeddings.embedder import embed_documents, embed_query
from app.generation.ollama_llm import generate
from app.ingestion.chunker import chunk_document
from app.ingestion.parser import parse_pdf
from app.models.schemas import (
    AskRequest,
    AskResponse,
    DocumentResponse,
    RetrievedChunk,
)
from app.retrieval.reranker import rerank
from app.retrieval.store import collection_exists, search, upsert_chunks
from app.citations.manager import verify_and_format


router = APIRouter()

UNAVAILABLE_MESSAGE = (
    "The answer is not available in the provided legal documents."
)
MAX_UPLOAD_BYTES = 25 * 1024 * 1024


# =========================================================
# Document registry helpers
# =========================================================


def _read_documents() -> List[dict]:
    try:
        data = json.loads(DOCUMENTS_FILE.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except (OSError, json.JSONDecodeError):
        return []


def _write_documents(documents: List[dict]) -> None:
    DOCUMENTS_FILE.write_text(
        json.dumps(documents, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def _slugify_filename(filename: str) -> str:
    stem = Path(filename).stem
    stem = re.sub(r"[^A-Za-z0-9_-]+", "-", stem).strip("-")
    return stem or "legal-document"


def _document_name(filename: str) -> str:
    return Path(filename).stem.replace("_", " ").replace("-", " ").strip().title()


def _append_chunks(chunks: List[dict]) -> None:
    if not chunks:
        return

    with CHUNKS_FILE.open("a", encoding="utf-8") as handle:
        for chunk in chunks:
            handle.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def _find_document(document_id: str):
    return next(
        (item for item in _read_documents() if item.get("document_id") == document_id),
        None,
    )


# =========================================================
# Health
# =========================================================


@router.get("/health")
def health():
    return {
        "status": "ok",
        "collection_ready": collection_exists(),
    }


# =========================================================
# PDF upload + automatic ingestion
# =========================================================


@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload one PDF, extract its text, create legal-aware chunks,
    generate embeddings, and add the chunks to the shared Qdrant index.
    """

    filename = file.filename or "document.pdf"

    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    content = await file.read()

    if not content:
        raise HTTPException(status_code=400, detail="The uploaded PDF is empty.")

    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="PDF is too large. Maximum supported size is 25 MB.",
        )

    document_id = str(uuid.uuid4())
    stored_name = f"{document_id}.pdf"
    stored_path = UPLOADS_DIR / stored_name
    stored_path.write_bytes(content)

    document_name = _document_name(filename)
    source_file = filename

    try:
        pages = parse_pdf(stored_path)

        if not pages:
            raise ValueError("No pages could be read from the PDF.")

        chunks = chunk_document(
            pages=pages,
            document_id=document_id,
            document_title=document_name,
            document_name=document_name,
            source_file=source_file,
            strategy=CHUNKING_STRATEGY,
            fixed_tokens=FIXED_CHUNK_TOKENS,
            overlap_percent=CHUNK_OVERLAP_PERCENT,
            target_words=CHUNK_TARGET_WORDS,
        )

        if not chunks:
            raise ValueError(
                "No searchable text was extracted from this PDF. "
                "If it is a scanned PDF, OCR is required before upload."
            )

        for chunk in chunks:
            chunk["document_type"] = "uploaded_legal_document"

        texts = [chunk["text"] for chunk in chunks]
        embeddings = embed_documents(texts)

        if embeddings is None or len(embeddings) == 0:
            raise ValueError("Embedding generation returned no vectors.")

        upsert_chunks(chunks, embeddings)
        _append_chunks(chunks)

        record = {
            "document_id": document_id,
            "filename": filename,
            "document_name": document_name,
            "document_type": "uploaded_legal_document",
            "page_count": len(pages),
            "chunk_count": len(chunks),
            "size_bytes": len(content),
            "stored_name": stored_name,
            "file_url": f"/api/documents/{document_id}/file",
        }

        documents = _read_documents()
        documents.append(record)
        _write_documents(documents)

        return DocumentResponse(**{k: record[k] for k in DocumentResponse.model_fields})

    except Exception as exc:
        try:
            stored_path.unlink(missing_ok=True)
        except OSError:
            pass

        raise HTTPException(
            status_code=400,
            detail=f"Could not process the PDF: {exc}",
        ) from exc


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: str):
    document = _find_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    return DocumentResponse(**{k: document[k] for k in DocumentResponse.model_fields})


@router.get("/documents/{document_id}/file")
def get_document_file(document_id: str):
    document = _find_document(document_id)

    if not document:
        raise HTTPException(status_code=404, detail="Document not found.")

    path = UPLOADS_DIR / document["stored_name"]

    if not path.exists():
        raise HTTPException(status_code=404, detail="Stored PDF file not found.")

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=document["filename"],
        content_disposition_type="inline",
    )


# =========================================================
# RAG question answering
# =========================================================


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest):
    if not collection_exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "Vector index is not ready. Upload a PDF first or run: "
                "python scripts/ingest.py"
            ),
        )

    start = time.perf_counter()

    qvec = embed_query(request.question)

    initial_k = request.top_k or INITIAL_TOP_K
    document_id = request.document_id or request.document

    points = search(
        qvec,
        limit=initial_k,
        score_threshold=SIMILARITY_THRESHOLD,
        document=document_id,
    )

    if not points:
        return AskResponse(
            answer=UNAVAILABLE_MESSAGE,
            sources=[],
            retrieved_chunks=[],
            answerable=False,
        )

    use_reranker = (
        ENABLE_RERANKER
        if request.rerank is None
        else request.rerank
    )

    if use_reranker:
        ranked = rerank(
            request.question,
            points,
            request.top_k or FINAL_TOP_K,
        )

        contexts = [point.payload for point, _ in ranked]
        scores = {
            point.payload["chunk_id"]: score
            for point, score in ranked
        }
    else:
        selected_points = points[: request.top_k or FINAL_TOP_K]
        contexts = [point.payload for point in selected_points]
        scores = {
            point.payload["chunk_id"]: float(point.score)
            for point in selected_points
        }

    best_dense = max(float(point.score) for point in points)

    if best_dense < SIMILARITY_THRESHOLD:
        return AskResponse(
            answer=UNAVAILABLE_MESSAGE,
            sources=[],
            retrieved_chunks=[],
            answerable=False,
        )

    try:
        raw_answer = generate(request.question, contexts)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Sarvam API generation failed: {exc}",
        ) from exc

    if UNAVAILABLE_MESSAGE in raw_answer:
        answerable = False
        clean_answer = raw_answer
        sources = []
    else:
        answerable = True
        clean_answer, sources = verify_and_format(raw_answer, contexts)

    retrieved = []

    for context in contexts:
        retrieved.append(
            RetrievedChunk(
                chunk_id=context["chunk_id"],
                document_id=context.get("document_id"),
                document=context["document_name"],
                page=context["page_start"],
                page_end=context["page_end"],
                section=(
                    context.get("heading_path")
                    or context.get("section")
                    or context.get("subsection")
                    or context.get("chapter")
                    or "N/A"
                ),
                score=round(float(scores.get(context["chunk_id"], 0)), 4),
                text=context["text"],
            )
        )

    _ = time.perf_counter() - start

    return AskResponse(
        answer=clean_answer,
        sources=sources,
        retrieved_chunks=retrieved,
        answerable=answerable,
    )

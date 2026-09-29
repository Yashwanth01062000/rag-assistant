from typing import List, Optional

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=2)
    top_k: Optional[int] = Field(default=None, ge=1, le=20)
    # New field used by the upload -> PDF + chat workflow.
    document_id: Optional[str] = None
    # Backward-compatible alias for the previous API.
    document: Optional[str] = None
    rerank: Optional[bool] = None


class Source(BaseModel):
    citation: int
    chunk_id: str
    document_id: Optional[str] = None
    document: str
    page: int
    page_end: int
    section: str
    source_file: str


class RetrievedChunk(BaseModel):
    chunk_id: str
    document_id: Optional[str] = None
    document: str
    page: int
    page_end: int
    section: str
    score: float
    text: str


class AskResponse(BaseModel):
    answer: str
    sources: List[Source]
    retrieved_chunks: List[RetrievedChunk]
    answerable: bool


class DocumentResponse(BaseModel):
    document_id: str
    filename: str
    document_name: str
    document_type: str
    page_count: int
    chunk_count: int
    size_bytes: int
    file_url: str

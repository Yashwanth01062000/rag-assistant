from functools import lru_cache
from typing import List

from sentence_transformers import SentenceTransformer

from app.config import EMBEDDING_MODEL


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_documents(texts: List[str]):
    model = get_model()
    if hasattr(model, "encode_document"):
        return model.encode_document(texts, normalize_embeddings=True, show_progress_bar=True)
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=True)


def embed_query(text: str):
    model = get_model()
    if hasattr(model, "encode_query"):
        return model.encode_query(text, normalize_embeddings=True)
    return model.encode(text, normalize_embeddings=True)

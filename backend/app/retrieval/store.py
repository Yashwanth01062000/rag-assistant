import uuid
from functools import lru_cache
from typing import Dict, List, Optional

from qdrant_client import QdrantClient, models

from app.config import COLLECTION_NAME, QDRANT_PATH


@lru_cache(maxsize=1)
def get_client() -> QdrantClient:
    return QdrantClient(path=str(QDRANT_PATH))


def collection_exists() -> bool:
    return get_client().collection_exists(COLLECTION_NAME)


def ensure_collection(vector_size: int):
    client = get_client()
    if not client.collection_exists(COLLECTION_NAME):
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE,
            ),
        )


def stable_uuid(chunk_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, chunk_id))


def upsert_chunks(chunks: List[Dict], embeddings):
    if not chunks or len(embeddings) == 0:
        return

    client = get_client()
    ensure_collection(len(embeddings[0]))

    points = []

    for chunk, vector in zip(chunks, embeddings):
        payload = dict(chunk)

        vector_data = (
            vector.tolist()
            if hasattr(vector, "tolist")
            else list(vector)
        )

        points.append(
            models.PointStruct(
                id=stable_uuid(chunk["chunk_id"]),
                vector=vector_data,
                payload=payload,
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
        wait=True,
    )


def search(
    query_vector,
    limit: int,
    score_threshold: Optional[float] = None,
    document: Optional[str] = None,
):
    """
    Search the shared legal collection.

    `document` is treated as a document_id for the new upload workflow.
    The filter is intentionally only applied when a document was supplied;
    this preserves the existing unfiltered /api/ask behavior.
    """

    client = get_client()
    query_filter = None

    if document:
        query_filter = models.Filter(
            must=[
                models.FieldCondition(
                    key="document_id",
                    match=models.MatchValue(value=document),
                )
            ]
        )

    result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector.tolist(),
        query_filter=query_filter,
        with_payload=True,
        limit=limit,
        score_threshold=score_threshold,
    )

    return result.points

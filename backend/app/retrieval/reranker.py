# Optional reranker. Disabled by default on low-memory machines.
from functools import lru_cache
from sentence_transformers import CrossEncoder

from app.config import RERANKER_MODEL


@lru_cache(maxsize=1)
def get_reranker():
    return CrossEncoder(RERANKER_MODEL, device="cpu")


def rerank(question, points, final_k):
    if not points:
        return []
    pairs = [(question, p.payload.get("text", "")) for p in points]
    scores = get_reranker().predict(pairs, batch_size=2, show_progress_bar=False)
    ranked = sorted(zip(points, scores), key=lambda x: float(x[1]), reverse=True)
    return [(p, float(score)) for p, score in ranked[:final_k]]

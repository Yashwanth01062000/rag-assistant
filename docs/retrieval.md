# Retrieval strategy

Baseline retrieval uses cosine similarity in Qdrant. The default pipeline retrieves 12 candidates, applies a similarity threshold, and reranks the candidates with `BAAI/bge-reranker-base` before passing the top 5 to the LLM.

The implementation supports metadata filtering by document name.

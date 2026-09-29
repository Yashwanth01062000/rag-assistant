# Architecture

The system is a local RAG pipeline:

1. PDF ingestion extracts text page-by-page and detects likely headings.
2. Section-aware chunking preserves document, chapter, section, subsection and page metadata.
3. Sentence Transformers creates dense embeddings.
4. Qdrant stores vectors and metadata.
5. A query is embedded and matched against Qdrant.
6. Optional CrossEncoder reranking improves the candidate order.
7. A retrieval threshold provides an answerability gate.
8. Ollama generates an answer only from retrieved context.
9. Citation markers reference retrieved chunk IDs; the backend resolves those IDs to verified metadata.
10. React displays the answer, sources and retrieved chunks.

from app.ingestion.chunker import chunk_document


def test_section_aware_chunking():
    pages = [{"page": 1, "lines": [
        {"text": "4.0 System Design", "is_heading": True},
        {"text": "Technical requirements are developed from stakeholder needs." * 20, "is_heading": False},
        {"text": "4.2 Technical Requirements Definition", "is_heading": True},
        {"text": "Requirements are captured and managed." * 20, "is_heading": False},
    ]}]
    chunks = chunk_document(pages, "doc", "Test Document", "test.pdf", 50, 10)
    assert chunks
    assert any("4.2 Technical Requirements Definition" in c["section"] for c in chunks)

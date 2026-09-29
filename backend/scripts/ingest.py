import json
import sys

from pathlib import Path


# =========================================================
# PROJECT PATH
# =========================================================

ROOT = Path(
    __file__
).resolve().parents[2]

BACKEND = ROOT / "backend"

sys.path.insert(
    0,
    str(BACKEND),
)


# =========================================================
# CONFIG
# =========================================================

from app.config import (
    RAW_DIR,
    CHUNKS_FILE,
    COLLECTION_NAME,
    QDRANT_PATH,
    CHUNKING_STRATEGY,
    FIXED_CHUNK_TOKENS,
    CHUNK_OVERLAP_PERCENT,
)


# =========================================================
# PDF PARSER
# =========================================================

from app.ingestion.parser import (
    parse_pdf,
)


# =========================================================
# CHUNKER
# =========================================================

from app.ingestion.chunker import (
    chunk_document,
)


# =========================================================
# EMBEDDINGS
# =========================================================

from app.embeddings.embedder import (
    embed_documents,
)


# =========================================================
# QDRANT
# =========================================================

from app.retrieval.store import (
    get_client,
    stable_uuid,
    ensure_collection,
)

from qdrant_client import models


# =========================================================
# LEGAL DOCUMENT MAP
# =========================================================

DOC_MAP = {

    "commercial_services_agreement.pdf": (
        "commercial-services-agreement",
        "Commercial Services Agreement",
        "commercial_contract",
    ),

    "software_license_agreement.pdf": (
        "software-license-agreement",
        "Software License Agreement",
        "software_license",
    ),
}


# =========================================================
# DOCUMENT METADATA
# =========================================================

def get_document_metadata(
    pdf: Path,
):

    if pdf.name in DOC_MAP:

        return DOC_MAP[
            pdf.name
        ]

    document_id = (
        pdf.stem
        .lower()
        .replace(
            " ",
            "-",
        )
        .replace(
            "_",
            "-",
        )
    )

    document_name = (
        pdf.stem.replace(
            "_",
            " ",
        )
    )

    return (
        document_id,
        document_name,
        "legal_document",
    )


# =========================================================
# MAIN INGESTION
# =========================================================

def main():

    # -----------------------------------------------------
    # Find PDFs
    # -----------------------------------------------------

    pdfs = sorted(
        RAW_DIR.glob(
            "*.pdf"
        )
    )

    if not pdfs:

        raise SystemExit(
            f"No PDFs found in {RAW_DIR}"
        )

    print(
        "\nLegal Document Ingestion"
    )

    print(
        "=" * 60
    )

    print(
        f"Chunking strategy : "
        f"{CHUNKING_STRATEGY}"
    )

    print(
        f"Fixed chunk tokens: "
        f"{FIXED_CHUNK_TOKENS}"
    )

    print(
        f"Overlap           : "
        f"{CHUNK_OVERLAP_PERCENT}%"
    )

    print(
        f"Collection        : "
        f"{COLLECTION_NAME}"
    )

    print(
        "=" * 60
    )


    # -----------------------------------------------------
    # Store all chunks
    # -----------------------------------------------------

    all_chunks = []


    # =====================================================
    # PROCESS EACH PDF
    # =====================================================

    for pdf in pdfs:

        (
            document_id,
            document_name,
            document_type,
        ) = get_document_metadata(
            pdf
        )

        print(
            f"\nParsing: "
            f"{pdf.name}"
        )


        # -------------------------------------------------
        # Parse PDF
        # -------------------------------------------------

        pages = parse_pdf(
            pdf
        )

        print(
            f"  Pages extracted: "
            f"{len(pages)}"
        )


        # -------------------------------------------------
        # Create chunks
        # -------------------------------------------------

        chunks = chunk_document(

            pages=pages,

            document_id=document_id,

            document_title=document_name,

            document_name=document_name,

            source_file=pdf.name,

            strategy=CHUNKING_STRATEGY,

            fixed_tokens=(
                FIXED_CHUNK_TOKENS
            ),

            overlap_percent=(
                CHUNK_OVERLAP_PERCENT
            ),

            target_words=450,
        )


        # -------------------------------------------------
        # Add document type
        # -------------------------------------------------

        for chunk in chunks:

            chunk[
                "document_type"
            ] = document_type


        print(
            f"  Chunks created: "
            f"{len(chunks)}"
        )


        # -------------------------------------------------
        # Add to global list
        # -------------------------------------------------

        all_chunks.extend(
            chunks
        )


    # =====================================================
    # VALIDATE CHUNKS
    # =====================================================

    if not all_chunks:

        raise SystemExit(
            "No chunks were created "
            "from the legal documents."
        )


    # =====================================================
    # SAVE CHUNKS
    # =====================================================

    with CHUNKS_FILE.open(
        "w",
        encoding="utf-8",
    ) as f:

        for chunk in all_chunks:

            f.write(
                json.dumps(
                    chunk,
                    ensure_ascii=False,
                )
                + "\n"
            )


    print(
        f"\nSaved chunks to: "
        f"{CHUNKS_FILE}"
    )


    # =====================================================
    # EMBEDDINGS
    # =====================================================

    print(
        f"\nEmbedding "
        f"{len(all_chunks)} chunks..."
    )


    texts = [
        chunk["text"]
        for chunk in all_chunks
    ]


    embeddings = embed_documents(
        texts
    )


    # -----------------------------------------------------
    # Validate embeddings
    # -----------------------------------------------------

    if embeddings is None:

        raise SystemExit(
            "Embedding generation "
            "returned no vectors."
        )


    if len(embeddings) == 0:

        raise SystemExit(
            "Embedding generation "
            "returned no vectors."
        )


    # =====================================================
    # QDRANT CLIENT
    # =====================================================

    client = get_client()


    # =====================================================
    # DELETE OLD COLLECTION
    # =====================================================

    if client.collection_exists(
        COLLECTION_NAME
    ):

        print(
            f"\nDeleting existing "
            f"collection: "
            f"{COLLECTION_NAME}"
        )

        client.delete_collection(
            COLLECTION_NAME
        )


    # =====================================================
    # CREATE COLLECTION
    # =====================================================

    ensure_collection(
        len(
            embeddings[0]
        )
    )


    # =====================================================
    # CREATE QDRANT POINTS
    # =====================================================

    points = []


    for chunk, vector in zip(
        all_chunks,
        embeddings,
    ):

        # -------------------------------------------------
        # Convert numpy vector to list
        # -------------------------------------------------

        if hasattr(
            vector,
            "tolist",
        ):

            vector_data = (
                vector.tolist()
            )

        else:

            vector_data = list(
                vector
            )


        points.append(
            models.PointStruct(

                id=stable_uuid(
                    chunk[
                        "chunk_id"
                    ]
                ),

                vector=vector_data,

                payload=chunk,
            )
        )


    # =====================================================
    # INSERT INTO QDRANT
    # =====================================================

    batch_size = 64


    for i in range(
        0,
        len(points),
        batch_size,
    ):

        batch = points[
            i:
            i + batch_size
        ]


        client.upsert(

            collection_name=(
                COLLECTION_NAME
            ),

            points=batch,

            wait=True,
        )


        indexed_count = min(
            i + batch_size,
            len(points),
        )


        print(
            f"Indexed "
            f"{indexed_count}"
            f"/{len(points)}"
        )


    # =====================================================
    # COMPLETE
    # =====================================================

    print(
        "\n" + "=" * 60
    )

    print(
        "LEGAL DOCUMENT "
        "INGESTION COMPLETE"
    )

    print(
        "=" * 60
    )


    print(
        f"Documents : "
        f"{len(pdfs)}"
    )

    print(
        f"Chunks    : "
        f"{len(all_chunks)}"
    )

    print(
        f"Collection: "
        f"{COLLECTION_NAME}"
    )

    print(
        f"Qdrant    : "
        f"{QDRANT_PATH}"
    )

    print(
        f"Chunks    : "
        f"{CHUNKS_FILE}"
    )

    print(
        f"Strategy  : "
        f"{CHUNKING_STRATEGY}"
    )

    print(
        f"Overlap   : "
        f"{CHUNK_OVERLAP_PERCENT}%"
    )

    print(
        "=" * 60
    )


# =========================================================
# ENTRY POINT
# =========================================================

if __name__ == "__main__":
    main()
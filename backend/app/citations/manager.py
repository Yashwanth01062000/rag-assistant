import re
from typing import Dict, List, Tuple


CITATION_PATTERN = re.compile(r"\[CITATION:\s*([^\]]+)\]")


def verify_and_format(
    answer: str,
    contexts: List[Dict],
) -> Tuple[str, List[Dict]]:

    by_id = {c["chunk_id"]: c for c in contexts}
    cited_ids = []

    for chunk_id in CITATION_PATTERN.findall(answer):
        chunk_id = chunk_id.strip()

        if chunk_id in by_id and chunk_id not in cited_ids:
            cited_ids.append(chunk_id)

    number_map = {
        cid: i + 1
        for i, cid in enumerate(cited_ids)
    }

    def replace_citation(match):
        chunk_id = match.group(1).strip()
        return f"[{number_map[chunk_id]}]" if chunk_id in number_map else ""

    clean_answer = CITATION_PATTERN.sub(replace_citation, answer)

    source_ids = (
        cited_ids
        if cited_ids
        else [c["chunk_id"] for c in contexts]
    )

    sources = []

    for i, cid in enumerate(source_ids, start=1):
        c = by_id[cid]

        sources.append(
            {
                "citation": i,
                "chunk_id": cid,
                "document_id": c.get("document_id"),
                "document": c["document_name"],
                "page": c["page_start"],
                "page_end": c["page_end"],
                "section": (
                    c.get("heading_path")
                    or c.get("section")
                    or c.get("subsection")
                    or c.get("chapter")
                    or "N/A"
                ),
                "source_file": c["source_file"],
            }
        )

    return clean_answer, sources

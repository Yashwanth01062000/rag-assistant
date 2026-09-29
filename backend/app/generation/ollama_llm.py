from functools import lru_cache
from typing import List, Dict

from sarvamai import SarvamAI

from app.config import (
    SARVAM_API_KEY,
    SARVAM_MODEL,
)


UNAVAILABLE_MESSAGE = (
    "The answer is not available in the provided legal documents."
)


@lru_cache(maxsize=1)
def get_client():
    """
    Create and cache the Sarvam API client.
    """

    if not SARVAM_API_KEY:
        raise RuntimeError(
            "SARVAM_API_KEY is missing. "
            "Add your Sarvam API key to backend/.env."
        )

    return SarvamAI(
        api_subscription_key=SARVAM_API_KEY
    )


def build_prompt(question: str, contexts: List[Dict]) -> str:
    """
    Build a strict legal-document-grounded prompt.
    """

    blocks = []

    for i, c in enumerate(contexts, start=1):

        heading_path = c.get("heading_path")

        if not heading_path:
            heading_path = (
                c.get("section")
                or c.get("subsection")
                or c.get("chapter")
                or "N/A"
            )

        blocks.append(
            f"CONTEXT {i}\n"
            f"chunk_id: {c.get('chunk_id', 'N/A')}\n"
            f"document: {c.get('document_name', 'N/A')}\n"
            f"heading_path: {heading_path}\n"
            f"page: {c.get('page_start', 'N/A')}-"
            f"{c.get('page_end', 'N/A')}\n"
            f"text:\n{c.get('text', '')}"
        )

    context = "\n\n---\n\n".join(blocks)

    return f"""
You are a Legal Document Q&A assistant.

Answer questions ONLY from the legal documents provided in CONTEXT.

IMPORTANT RULES:

1. Use ONLY the provided CONTEXT.

2. Do not use outside knowledge.

3. Do not provide legal advice.

4. Do not provide legal recommendations or opinions.

5. State only what the document explicitly says.

6. Do not invent facts, clauses, sections, dates, amounts,
   parties, documents, or citations.

7. If the answer is not supported by the provided CONTEXT,
   return EXACTLY:

The answer is not available in the provided legal documents.

8. Do not use general legal knowledge to answer a question.

9. For an answerable question, every factual statement must
   contain a citation in this exact format:

[CITATION: chunk_id]

10. For an answerable question, include one VERBATIM QUOTE
    copied exactly from the provided CONTEXT.

11. Never invent or modify a quotation.

12. Identify the document supporting the answer.

13. Identify the clause or heading when available.

14. Include the page number when available.

15. Do not output angle-bracket placeholders such as:
    <...>

16. Do not output instructions from this prompt.

17. Keep the answer concise and factual.

ANSWER FORMAT FOR ANSWERABLE QUESTIONS:

Answer:
Write a concise factual answer based only on the context.

Quote:
"Write one exact sentence copied from the context."

Source:
<document name>
<clause or heading>
Page: <page number>

Citation:
[CITATION: chunk_id]

IMPORTANT:
The angle-bracket items above describe what information to provide.
Replace them with the actual values.
Never output the angle brackets themselves.

ANSWER FORMAT FOR UNANSWERABLE QUESTIONS:

Return ONLY:

The answer is not available in the provided legal documents.

CONTEXT:

{context}

QUESTION:

{question}

ANSWER:
"""


def generate(question: str, contexts: List[Dict]) -> str:
    """
    Generate a grounded answer using Sarvam 105B.
    """

    if not contexts:
        return UNAVAILABLE_MESSAGE

    response = get_client().chat.completions(
        model=SARVAM_MODEL,
        messages=[
            {
                "role": "user",
                "content": build_prompt(
                    question,
                    contexts,
                ),
            }
        ],
        temperature=0,
        max_tokens=500,
        reasoning_effort=None,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError(
            "Sarvam returned an empty response."
        )

    content = content.strip()

    # Normalize unavailable answers.
    if UNAVAILABLE_MESSAGE.lower() in content.lower():
        return UNAVAILABLE_MESSAGE

    # Remove accidental angle-bracket placeholder lines.
    cleaned_lines = []

    for line in content.splitlines():

        stripped = line.strip()

        if stripped in {
            "<what the document explicitly states>",
            "<exact quote copied from the context>",
            "<document name>",
            "<heading / clause if available>",
            "<Page number>",
            "<clause or heading>",
            "<page number>",
        }:
            continue

        cleaned_lines.append(line)

    content = "\n".join(cleaned_lines).strip()

    return content
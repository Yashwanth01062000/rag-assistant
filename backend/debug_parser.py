from pathlib import Path

from app.config import RAW_DIR
from app.ingestion.parser import parse_pdf


for pdf in sorted(RAW_DIR.glob("*.pdf")):

    print("\n" + "=" * 70)
    print("FILE:", pdf.name)
    print("=" * 70)

    pages = parse_pdf(pdf)

    print("Pages:", len(pages))

    for page in pages:

        print("\nPAGE:", page["page"])
        print("Number of lines:", len(page["lines"]))

        for i, line in enumerate(page["lines"], start=1):

            print(
                f"{i:03d} | "
                f"heading={line.get('is_heading')} | "
                f"{line.get('text')}"
            )
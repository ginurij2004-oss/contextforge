from pathlib import Path

from pypdf import PdfReader


def extract_pdf_pages(
    file_path: Path
) -> list[dict]:

    reader = PdfReader(
        str(file_path)
    )

    pages = []

    for page_number, page in enumerate(
        reader.pages,
        start=1
    ):

        text = page.extract_text() or ""

        text = text.strip()

        if not text:
            continue

        pages.append({
            "page": page_number,
            "text": text,
        })

    return pages
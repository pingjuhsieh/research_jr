"""Convert eHRAF PDFs to markdown via markitdown."""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

_V2_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _V2_ROOT.parent
_PIPELINE_ROOT = _CODE_ROOT.parent
for _p in (_CODE_ROOT, _PIPELINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from llm_ehraf.config import ensure_dirs
from llm_ehraf.db import connect_db
from llm_ehraf.doc_utils import (
    doc_id_from_pdf,
    ethnography_group_from_doc_id,
    list_pdfs,
    markdown_path_for_doc,
)
from llm_ehraf.markdown import clean_markdown


def convert_pdf(pdf_path: Path) -> str:
    try:
        from markitdown import MarkItDown
    except ImportError as exc:
        raise RuntimeError(
            "markitdown is not installed. Run: uv sync (or uv add 'markitdown[pdf]')"
        ) from exc

    converter = MarkItDown(enable_plugins=False)
    result = converter.convert_local(str(pdf_path))
    return result.text_content or ""


def run_convert(
    *,
    pdf_root: Path,
    db_path: Path,
    force: bool = False,
    limit: int | None = None,
    region: str | None = None,
    group: str | None = None,
) -> None:
    paths = ensure_dirs()
    con = connect_db(db_path)

    pdf_items = list_pdfs(pdf_root)
    if region:
        pdf_items = [(p, r) for p, r in pdf_items if r == region]
    if group:
        pdf_items = [
            (p, r) for p, r in pdf_items
            if ethnography_group_from_doc_id(doc_id_from_pdf(p)).lower() == group.lower()
        ]
    if not pdf_items:
        raise RuntimeError(f"No PDFs found under {pdf_root}")

    if limit is not None:
        pdf_items = pdf_items[:limit]

    existing = {
        row["doc_id"]
        for row in con.execute("SELECT doc_id FROM document WHERE md_clean_path IS NOT NULL")
    }

    print(f"PDF root: {pdf_root}")
    print(f"Found {len(pdf_items)} PDFs")

    converted = 0
    for pdf_path, region in tqdm(pdf_items, desc="Convert PDF→MD"):
        doc_id = doc_id_from_pdf(pdf_path)
        if doc_id in existing and not force:
            continue

        raw_md = convert_pdf(pdf_path)
        raw_path = markdown_path_for_doc(paths, doc_id, cleaned=False)
        clean_path = markdown_path_for_doc(paths, doc_id, cleaned=True)
        raw_path.write_text(raw_md, encoding="utf-8")

        cleaned = clean_markdown(raw_md)
        clean_path.write_text(cleaned, encoding="utf-8")

        ethno = ethnography_group_from_doc_id(doc_id)
        now = datetime.now(timezone.utc).isoformat()
        con.execute(
            """
            INSERT INTO document (
              doc_id, filename, region, ethnography_group_name, pdf_path,
              md_raw_path, md_clean_path, char_count, converted_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(doc_id) DO UPDATE SET
              filename=excluded.filename,
              region=excluded.region,
              ethnography_group_name=excluded.ethnography_group_name,
              pdf_path=excluded.pdf_path,
              md_raw_path=excluded.md_raw_path,
              md_clean_path=excluded.md_clean_path,
              char_count=excluded.char_count,
              converted_at=excluded.converted_at
            """,
            (
                doc_id,
                pdf_path.name,
                region,
                ethno,
                str(pdf_path.resolve()),
                str(raw_path),
                str(clean_path),
                len(cleaned),
                now,
            ),
        )
        converted += 1

    con.commit()
    con.close()
    print(f"Converted {converted} documents → {paths.markdown_clean}")


def main() -> None:
    paths = ensure_dirs()
    parser = argparse.ArgumentParser(description="PDF → markdown (markitdown)")
    parser.add_argument("--pdf-root", type=Path, default=paths.ethnography_pages)
    parser.add_argument("--db", type=Path, default=paths.jr_sqlite)
    parser.add_argument("--force", action="store_true", help="Re-convert documents already in DB")
    parser.add_argument("--limit", type=int, default=None, help="Process only first N PDFs (for testing)")
    parser.add_argument("--region", type=str, default=None, help="Filter by region folder (e.g. WesternAfrica)")
    parser.add_argument("--group", type=str, default=None, help="Filter by ethnography group (e.g. Hausa)")
    args = parser.parse_args()
    run_convert(
        pdf_root=args.pdf_root,
        db_path=args.db,
        force=args.force,
        limit=args.limit,
        region=args.region,
        group=args.group,
    )


if __name__ == "__main__":
    main()

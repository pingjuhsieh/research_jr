#!/usr/bin/env python3
"""CLI entry point for the joking-relationship database builder."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_JR_DB_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _JR_DB_ROOT.parent
_PIPELINE_ROOT = _CODE_ROOT.parent
for _p in (_CODE_ROOT, _PIPELINE_ROOT):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from llm_ehraf.config import ensure_dirs
from llm_ehraf.convert import run_convert
from llm_ehraf.export import run_export
from llm_ehraf.extract import run_extract


def main() -> None:
    paths = ensure_dirs()
    parser = argparse.ArgumentParser(
        description="ICMID joking-relationship database builder (markitdown + full-doc LLM)"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_convert = sub.add_parser("convert", help="PDF → markdown_raw + markdown_clean")
    p_convert.add_argument("--pdf-root", type=Path, default=paths.ethnography_pages)
    p_convert.add_argument("--db", type=Path, default=paths.jr_sqlite)
    p_convert.add_argument("--force", action="store_true")
    p_convert.add_argument("--limit", type=int, default=None)
    p_convert.add_argument("--region", type=str, default=None)
    p_convert.add_argument("--group", type=str, default=None)

    p_extract = sub.add_parser("extract", help="LLM extract joking relationships")
    p_extract.add_argument("--db", type=Path, default=paths.jr_sqlite)
    p_extract.add_argument("--force", action="store_true")
    p_extract.add_argument("--doc-id", type=str, default=None)
    p_extract.add_argument("--region", type=str, default=None)
    p_extract.add_argument("--group", type=str, default=None)
    p_extract.add_argument("--limit", type=int, default=None)
    p_extract.add_argument("--dry-run", action="store_true")

    p_export = sub.add_parser("export", help="Export Visualization-compatible CSVs")
    p_export.add_argument("--db", type=Path, default=paths.jr_sqlite)
    p_export.add_argument("--export-dir", type=Path, default=None)
    p_export.add_argument("--copy-to-visualization", action="store_true")

    p_all = sub.add_parser(
        "all",
        help="extract → export (add --convert for first-time PDF ingest)",
    )
    p_all.add_argument("--pdf-root", type=Path, default=paths.ethnography_pages)
    p_all.add_argument("--db", type=Path, default=paths.jr_sqlite)
    p_all.add_argument("--force", action="store_true")
    p_all.add_argument("--region", type=str, default=None)
    p_all.add_argument("--group", type=str, default=None)
    p_all.add_argument("--limit", type=int, default=None)
    p_all.add_argument("--dry-run", action="store_true")
    p_all.add_argument("--copy-to-visualization", action="store_true")
    p_all.add_argument("--convert", action="store_true", help="Run PDF convert before extract")

    args = parser.parse_args()

    if args.command == "convert":
        run_convert(
            pdf_root=args.pdf_root,
            db_path=args.db,
            force=args.force,
            limit=args.limit,
            region=args.region,
            group=args.group,
        )
    elif args.command == "extract":
        run_extract(
            db_path=args.db,
            force=args.force,
            doc_id=args.doc_id,
            region=args.region,
            group=args.group,
            limit=args.limit,
            dry_run=args.dry_run,
        )
    elif args.command == "export":
        run_export(
            db_path=args.db,
            export_dir=args.export_dir,
            copy_to_visualization=args.copy_to_visualization,
        )
    elif args.command == "all":
        if getattr(args, "convert", False):
            run_convert(
                pdf_root=args.pdf_root,
                db_path=args.db,
                force=args.force,
                limit=args.limit,
                region=args.region,
                group=args.group,
            )
        run_extract(
            db_path=args.db,
            force=args.force,
            region=args.region,
            group=args.group,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            run_export(
                db_path=args.db,
                copy_to_visualization=args.copy_to_visualization,
            )


if __name__ == "__main__":
    main()

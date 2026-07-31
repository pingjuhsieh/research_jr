"""Export SQLite results to Visualization-compatible CSVs."""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import Any

_V2_ROOT = Path(__file__).resolve().parent
_CODE_ROOT = _V2_ROOT.parent
_PIPELINE_ROOT = _CODE_ROOT.parent
_VIS_DIR = _CODE_ROOT / "visualization"
for _p in (_CODE_ROOT, _PIPELINE_ROOT, _VIS_DIR):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from llm_ehraf.aggregate import CSV_FIELDNAMES, aggregate_relationships  # noqa: E402
from llm_ehraf.config import ensure_dirs
from llm_ehraf.db import connect_db
from polygon_registry import canonicalize_entity_name  # noqa: E402

# Map v2 scope → legacy scope for concordance / Visualization
SCOPE_TO_LEGACY = {
    "cross_group": "between_groups",
    "within_group": "within_group",
    "kinship": "within_group",
}


def _load_rows(con, scope_filter: str | None = None) -> list[dict[str, Any]]:
    query = """
        SELECT
            relationship_row_id AS assertion_id,
            doc_id,
            region,
            ethnography_group_name,
            entity_a_raw,
            entity_a_type,
            entity_b_raw,
            entity_b_type,
            scope_coded,
            reasoning,
            supporting_quote_raw,
            relation_label_raw,
            local_term_raw,
            symmetry_coded,
            relation_type_coded,
            confidence,
            notes
        FROM joking_relationship
    """
    params: list[Any] = []
    if scope_filter:
        query += " WHERE scope_coded = ?"
        params.append(scope_filter)
    query += " ORDER BY doc_id, relationship_row_id"
    rows = con.execute(query, params).fetchall()
    out: list[dict[str, Any]] = []
    for r in rows:
        d = dict(r)
        legacy_scope = SCOPE_TO_LEGACY.get(d["scope_coded"], d["scope_coded"])
        quote = d.get("supporting_quote_raw") or ""
        doc_id = d.get("doc_id") or ""
        d["scope_coded"] = legacy_scope
        d["ethnography_group_name"] = d["ethnography_group_name"]
        d["explicit_flag"] = True
        d["page"] = ""
        d["quote_text"] = quote
        if doc_id and quote:
            d["supporting_quote_raw"] = f"{doc_id}::{quote}"
        out.append(d)
    return out


def _export_scope_csv(rows: list[dict[str, Any]], scope: str, out_path: Path, *, between_pair_only: bool) -> int:
    scoped = [r for r in rows if r["scope_coded"] == scope]
    aggregated = aggregate_relationships(scoped, scope, between_pair_only=between_pair_only)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CSV_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in aggregated:
            writer.writerow(row)
    return len(aggregated)


def _export_all_csv(con, out_path: Path) -> int:
    """Flat export with reasoning — one row per extracted assertion."""
    rows = con.execute(
        """
        SELECT
            relationship_row_id,
            doc_id,
            region,
            ethnography_group_name,
            entity_a_raw,
            entity_a_type,
            entity_b_raw,
            entity_b_type,
            scope_coded,
            reasoning,
            supporting_quote_raw,
            relation_label_raw,
            local_term_raw,
            symmetry_coded,
            relation_type_coded,
            confidence,
            notes,
            extracted_at
        FROM joking_relationship
        ORDER BY region, ethnography_group_name, doc_id, relationship_row_id
        """
    ).fetchall()

    fieldnames = [
        "relationship_row_id",
        "doc_id",
        "region",
        "ethnography_group",
        "entity_a",
        "entity_a_type",
        "entity_b",
        "entity_b_type",
        "scope_coded",
        "reasoning",
        "supporting_quote_raw",
        "relation_label_raw",
        "local_term_raw",
        "symmetry_coded",
        "relation_type_coded",
        "confidence",
        "notes",
        "extracted_at",
    ]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(
                {
                    "relationship_row_id": r["relationship_row_id"],
                    "doc_id": r["doc_id"],
                    "region": r["region"],
                    "ethnography_group": r["ethnography_group_name"],
                    "entity_a": canonicalize_entity_name(r["entity_a_raw"]),
                    "entity_a_type": r["entity_a_type"],
                    "entity_b": canonicalize_entity_name(r["entity_b_raw"]),
                    "entity_b_type": r["entity_b_type"],
                    "scope_coded": r["scope_coded"],
                    "reasoning": r["reasoning"],
                    "supporting_quote_raw": r["supporting_quote_raw"],
                    "relation_label_raw": r["relation_label_raw"],
                    "local_term_raw": r["local_term_raw"],
                    "symmetry_coded": r["symmetry_coded"],
                    "relation_type_coded": r["relation_type_coded"],
                    "confidence": r["confidence"],
                    "notes": r["notes"],
                    "extracted_at": r["extracted_at"],
                }
            )
    return len(rows)


def run_export(
    *,
    db_path: Path,
    export_dir: Path | None = None,
    copy_to_visualization: bool = False,
) -> None:
    paths = ensure_dirs()
    export_dir = export_dir or paths.export_dir
    con = connect_db(db_path)

    all_count = _export_all_csv(con, export_dir / "llm_ehraf_joking_relationships.csv")
    legacy_rows = _load_rows(con)
    within_n = _export_scope_csv(
        legacy_rows, "within_group", export_dir / "within_groups_for_review.csv", between_pair_only=False
    )
    between_n = _export_scope_csv(
        legacy_rows, "between_groups", export_dir / "between_groups_for_review.csv", between_pair_only=True
    )
    con.close()

    print(f"Exported {all_count} raw rows → llm_ehraf_joking_relationships.csv")
    print(f"Exported {within_n} within/kinship rows → within_groups_for_review.csv")
    print(f"Exported {between_n} cross-group rows → between_groups_for_review.csv")

    if copy_to_visualization:
        print(
            "Note: --copy-to-visualization is deprecated; "
            "code/visualization/merge_sources.py reads output/llm_ehraf/export/ directly."
        )


def main() -> None:
    paths = ensure_dirs()
    parser = argparse.ArgumentParser(description="Export CSVs for Visualization")
    parser.add_argument("--db", type=Path, default=paths.jr_sqlite)
    parser.add_argument("--export-dir", type=Path, default=None)
    parser.add_argument(
        "--copy-to-visualization",
        action="store_true",
        help="Deprecated no-op (kept for old scripts).",
    )
    args = parser.parse_args()
    run_export(
        db_path=args.db,
        export_dir=args.export_dir,
        copy_to_visualization=args.copy_to_visualization,
    )


if __name__ == "__main__":
    main()

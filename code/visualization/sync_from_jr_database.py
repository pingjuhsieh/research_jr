#!/usr/bin/env python3
"""Sync interactive-map inputs from the consolidated jr_database outputs.

Writes:
  output/visualization/between_group_joking.xlsx
  output/visualization/jr_records.json

Then run:
  uv run python -B code/visualization/build_cross_group_map.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

_VIS_DIR = Path(__file__).resolve().parent
_PIPELINE = _VIS_DIR.parent.parent
if str(_VIS_DIR) not in sys.path:
    sys.path.insert(0, str(_VIS_DIR))

from config import (  # noqa: E402
    BETWEEN_GROUP_JOKING_XLSX,
    DOC_LEVEL_JR_CSV,
    JR_RECORDS_JSON,
    OUTPUT_DIR,
    PIPELINE_ROOT,
    WITHIN_GROUPS_CSV,
)

ASSERTIONS_CSV = PIPELINE_ROOT / "output" / "jr_database" / "merge_cross_assertions.csv"
CROSS_GROUP_CSV = PIPELINE_ROOT / "output" / "result" / "cross_group.csv"

_SOURCE_LABEL = {
    "llm_ehraf": "eHRAF",
    "keerthana_analysis": "Keerthana",
    "keerthana_og": "Keerthana",
    "icmid_sheet1": "ICMID",
    "icmid_sheet2": "ICMID",
    "icmid_jr_pair": "ICMID",
}

_ILLEGAL_XLSX_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() == "nan":
        return ""
    return _ILLEGAL_XLSX_RE.sub("", s)


def _pair_key(a: str, b: str) -> str:
    x, y = a.casefold(), b.casefold()
    return f"{a}|{b}" if x <= y else f"{b}|{a}"


def _record_id(row: pd.Series, idx: int) -> str:
    rid = _clean(row.get("relationship_row_id"))
    if rid:
        try:
            f = float(rid)
            if f == int(f):
                return str(int(f))
        except ValueError:
            return rid
        return rid
    src = _clean(row.get("source_dataset")) or "row"
    return f"{src}:{idx}"


def build_jr_records(assertions: pd.DataFrame) -> dict[str, dict]:
    records: dict[str, dict] = {}
    for idx, row in assertions.iterrows():
        rid = _record_id(row, int(idx) if isinstance(idx, int) else len(records))
        src_ds = _clean(row.get("source_dataset"))
        doc_id = _clean(row.get("doc_id"))
        quote = _clean(row.get("quote"))
        records[rid] = {
            "id": rid,
            "source": _SOURCE_LABEL.get(src_ds, src_ds or "unknown"),
            "doc_id": doc_id,
            "source_pdf": f"{doc_id.strip('/').replace('/', '_')}.pdf" if doc_id else "",
            "source_url": _clean(row.get("source_url")),
            "source_citation": _clean(row.get("source_citation")),
            "source_page": _clean(row.get("source_page")),
            "ethnography_group": _clean(row.get("ethnography_group")),
            "region": _clean(row.get("region")),
            "entity_a": _clean(row.get("entity_a")),
            "entity_b": _clean(row.get("entity_b")),
            "entity_a_type": _clean(row.get("entity_a_type")),
            "entity_b_type": _clean(row.get("entity_b_type")),
            "scope_coded": "cross_group",
            "reasoning": _clean(row.get("notes")),
            "notes": _clean(row.get("notes")),
            "quote": quote,
            "relation_label": _clean(row.get("relation_type")),
            "local_term": "",
            "symmetry": _clean(row.get("symmetry")),
            "relation_type": _clean(row.get("relation_type")),
            "confidence": 0.0,
            "joking_source": src_ds,
        }
    return records


def _norm_rid(val) -> str:
    rid = _clean(val)
    if not rid:
        return ""
    try:
        f = float(rid)
        if f == int(f):
            return str(int(f))
    except ValueError:
        pass
    return rid


def build_within_jr_records() -> dict[str, dict]:
    """Kinship / within-group detail rows for the map panel (from eHRAF + within CSV)."""
    records: dict[str, dict] = {}

    if DOC_LEVEL_JR_CSV.is_file():
        df = pd.read_csv(DOC_LEVEL_JR_CSV)
        for _, row in df.iterrows():
            scope = _clean(row.get("scope_coded")).casefold().replace("-", "_")
            if scope not in {"kinship", "within_group"}:
                continue
            rid = _norm_rid(row.get("relationship_row_id"))
            if not rid:
                continue
            doc_id = _clean(row.get("doc_id"))
            notes = _clean(row.get("notes"))
            reasoning = _clean(row.get("reasoning")) or notes
            records[rid] = {
                "id": rid,
                "source": "eHRAF",
                "doc_id": doc_id,
                "source_pdf": f"{doc_id.strip('/').replace('/', '_')}.pdf" if doc_id else "",
                "source_url": "",
                "source_citation": "",
                "source_page": "",
                "ethnography_group": _clean(row.get("ethnography_group")),
                "region": _clean(row.get("region")),
                "entity_a": _clean(row.get("entity_a")),
                "entity_b": _clean(row.get("entity_b")),
                "entity_a_type": _clean(row.get("entity_a_type")),
                "entity_b_type": _clean(row.get("entity_b_type")),
                "scope_coded": scope,
                "reasoning": reasoning,
                "notes": notes or reasoning,
                "quote": _clean(row.get("supporting_quote_raw")),
                "relation_label": _clean(row.get("relation_label_raw")),
                "local_term": _clean(row.get("local_term_raw")),
                "symmetry": _clean(row.get("symmetry_coded")),
                "relation_type": _clean(row.get("relation_type_coded")),
                "confidence": float(row.get("confidence") or 0.0),
                "joking_source": "llm_ehraf",
            }

    # Fill gaps from the visualization within_group.csv (IDs the map already links).
    if WITHIN_GROUPS_CSV.is_file():
        wdf = pd.read_csv(WITHIN_GROUPS_CSV)
        wdf.columns = [c.strip().lower().replace(" ", "_") for c in wdf.columns]
        for _, row in wdf.iterrows():
            rid = _norm_rid(row.get("relationship_id") or row.get("relationship_row_id"))
            if not rid or rid in records:
                continue
            doc_id = _clean(row.get("source_docs") or row.get("doc_id"))
            quote = _clean(row.get("supporting_quote_raw") or row.get("quote"))
            scope = _clean(row.get("scope_coded")).casefold().replace("-", "_") or "within_group"
            a_type = _clean(row.get("entity_a_type")).lower()
            b_type = _clean(row.get("entity_b_type")).lower()
            if scope == "within_group" and ("kin" in a_type or "kin" in b_type):
                scope = "kinship"
            records[rid] = {
                "id": rid,
                "source": "eHRAF",
                "doc_id": doc_id,
                "source_pdf": f"{doc_id.strip('/').replace('/', '_')}.pdf" if doc_id else "",
                "source_url": "",
                "source_citation": "",
                "source_page": "",
                "ethnography_group": _clean(row.get("ethnography_group")),
                "region": _clean(row.get("region")),
                "entity_a": _clean(row.get("entity_a")),
                "entity_b": _clean(row.get("entity_b")),
                "entity_a_type": _clean(row.get("entity_a_type")),
                "entity_b_type": _clean(row.get("entity_b_type")),
                "scope_coded": scope,
                "reasoning": _clean(row.get("relation_labels")),
                "notes": _clean(row.get("relation_labels")),
                "quote": quote,
                "relation_label": _clean(row.get("relation_labels")),
                "local_term": _clean(row.get("local_terms")),
                "symmetry": _clean(row.get("symmetry_coded")),
                "relation_type": _clean(row.get("relation_type_coded")),
                "confidence": float(row.get("confidence_mean") or 0.0),
                "joking_source": _clean(row.get("joking_source")) or "ehraf_v2",
            }

    return records


def build_joking_table(assertions: pd.DataFrame, pairs: pd.DataFrame) -> pd.DataFrame:
    """One map row per assertion, with homeland columns from the pair table."""
    pair_lookup: dict[str, pd.Series] = {}
    for _, pr in pairs.iterrows():
        a, b = _clean(pr.get("entity_a")), _clean(pr.get("entity_b"))
        if a and b:
            pair_lookup[_pair_key(a, b)] = pr

    rows: list[dict] = []
    for idx, row in assertions.iterrows():
        a, b = _clean(row.get("entity_a")), _clean(row.get("entity_b"))
        if not a or not b:
            continue
        pr = pair_lookup.get(_pair_key(a, b))
        src_ds = _clean(row.get("source_dataset"))
        rid = _record_id(row, int(idx) if isinstance(idx, int) else len(rows))

        def _side(prefix: str, entity: str) -> dict:
            if pr is None:
                return {
                    f"{prefix}_homeland_status": "",
                    f"{prefix}_polygon_source": "",
                    f"{prefix}_polygon_id": "",
                    f"{prefix}_parent_group": "",
                    f"{prefix}_homeland_key": "",
                    f"{prefix}_region": _clean(row.get("region")),
                    f"{prefix}_resolve_source": "",
                }
            psrc = _clean(pr.get(f"{prefix}_polygon_source"))
            pid = _clean(pr.get(f"{prefix}_polygon_id"))
            status = "resolved" if psrc and pid else "unresolved"
            return {
                f"{prefix}_homeland_status": status,
                f"{prefix}_polygon_source": psrc,
                f"{prefix}_polygon_id": pid,
                f"{prefix}_parent_group": _clean(pr.get(f"{prefix}_display_name")),
                f"{prefix}_homeland_key": f"{psrc}:{pid}" if psrc and pid else "",
                f"{prefix}_region": _clean(pr.get("region")) or _clean(row.get("region")),
                f"{prefix}_resolve_source": _clean(pr.get(f"{prefix}_resolve_source")),
            }

        rec = {
            "relationship_row_id": rid,
            "entity_a": a,
            "entity_a_type": _clean(row.get("entity_a_type")) or "ethnic_group",
            "entity_b": b,
            "entity_b_type": _clean(row.get("entity_b_type")) or "ethnic_group",
            "region": _clean(row.get("region")) or (_clean(pr.get("region")) if pr is not None else ""),
            "ethnography_group": _clean(row.get("ethnography_group")),
            "relation_type": _clean(row.get("relation_type")),
            "relation_category": "",
            "symmetry": _clean(row.get("symmetry")),
            "joking_source": src_ds,
            "notes": _clean(row.get("notes")),
            "quote": _clean(row.get("quote")),
            "source_flags": _clean(pr.get("source_flags")) if pr is not None else src_ds,
            "homeland_complete": int(pr.get("homeland_complete") or 0) if pr is not None else 0,
        }
        rec.update(_side("entity_a", a))
        rec.update(_side("entity_b", b))
        rows.append(rec)
    return pd.DataFrame(rows)


def main() -> None:
    if not ASSERTIONS_CSV.is_file():
        print(f"Missing {ASSERTIONS_CSV}")
        print("Run first: uv run python -B code/jr_database/build_cross_group.py")
        sys.exit(1)
    if not CROSS_GROUP_CSV.is_file():
        print(f"Missing {CROSS_GROUP_CSV}")
        sys.exit(1)

    assertions = pd.read_csv(ASSERTIONS_CSV)
    pairs = pd.read_csv(CROSS_GROUP_CSV)
    print(f"Assertions: {len(assertions)}  pairs: {len(pairs)}")

    records = build_jr_records(assertions)
    within_records = build_within_jr_records()
    # Cross-group IDs win on collision (should be rare / empty).
    for rid, rec in within_records.items():
        records.setdefault(rid, rec)
    joking = build_joking_table(assertions, pairs)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with JR_RECORDS_JSON.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    joking.to_excel(BETWEEN_GROUP_JOKING_XLSX, index=False, sheet_name="between_group")

    n_src = pd.Series([r.get("source") for r in records.values()]).value_counts().to_dict()
    n_scope = pd.Series([r.get("scope_coded") for r in records.values()]).value_counts().to_dict()
    print(f"  → {JR_RECORDS_JSON}  ({len(records)} records · {n_src})")
    print(f"     scopes: {n_scope}")
    print(f"  → {BETWEEN_GROUP_JOKING_XLSX}  ({len(joking)} rows)")
    print("Next: uv run python -B code/visualization/build_cross_group_map.py")


if __name__ == "__main__":
    main()

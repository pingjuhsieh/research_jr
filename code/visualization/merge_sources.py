#!/usr/bin/env python3
"""
Merge Keerthana joking data with jr_database eHRAF export.

Keeps Keerthana non-eHRAF rows (joking_source = analysis | og).
Replaces Keerthana eHRAF rows (joking_source null) with v2 cross-group JR.
Replaces legacy block-pipeline within-group CSV with v2 kinship + within_group.

Usage (called from prepare.py):
    uv run python code/visualization/merge_sources.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_VIS_DIR = Path(__file__).resolve().parent
if str(_VIS_DIR) not in sys.path:
    sys.path.insert(0, str(_VIS_DIR))

import pandas as pd

from polygon_registry import canonicalize_entity_name, normalize_entity_for_pair

from config import (
    BETWEEN_GROUP_SOURCE_MERGED_XLSX,
    BETWEEN_GROUP_SOURCE_XLSX,
    DOC_LEVEL_JR_CSV,
    JR_RECORDS_JSON,
    REGION_ALIAS,
    REGION_COLORS,
    WITHIN_GROUPS_MERGED_CSV,
)

_ILLEGAL_XLSX_RE = re.compile(r"[\000-\010]|[\013-\014]|[\016-\037]")
_KEERTHANA_KEEP_SOURCES = frozenset({"analysis", "og"})


def _clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _excel_safe(val) -> str:
    return _ILLEGAL_XLSX_RE.sub("", _clean(val))


def _truncate(s: str, max_len: int = 500) -> str:
    s = _clean(s)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _norm_region(r: str) -> str:
    if r in REGION_COLORS:
        return r
    return REGION_ALIAS.get(r.lower(), r)


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted([normalize_entity_for_pair(a), normalize_entity_for_pair(b)]))


def _is_keerthana_ehraf_row(row: pd.Series) -> bool:
    """Keerthana eHRAF rows have no joking_source (null/empty)."""
    return not _clean(row.get("joking_source"))


def keerthana_non_ehraf(df: pd.DataFrame) -> pd.DataFrame:
    js = df["joking_source"].fillna("").astype(str).str.strip().str.lower()
    return df[js.isin(_KEERTHANA_KEEP_SOURCES)].copy()


def _v2_cross_rows(df_v2: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    for _, r in df_v2[df_v2["scope_coded"] == "cross_group"].iterrows():
        entity_a = canonicalize_entity_name(_excel_safe(r.get("entity_a")))
        entity_b = canonicalize_entity_name(_excel_safe(r.get("entity_b")))
        if not entity_a or not entity_b or entity_a == entity_b:
            continue
        rows.append({
            "entity_a": entity_a,
            "entity_a_type": _excel_safe(r.get("entity_a_type")),
            "entity_b": entity_b,
            "entity_b_type": _excel_safe(r.get("entity_b_type")),
            "regions": _norm_region(_excel_safe(r.get("region"))),
            "ethnography_groups": _excel_safe(r.get("ethnography_group")),
            "relation_types_coded": _excel_safe(r.get("relation_type_coded")),
            "relation_categories": "",
            "symmetry": _excel_safe(r.get("symmetry_coded")),
            "joking_source": "ehraf_v2",
            "notes": _truncate(r.get("reasoning")),
            "relationship_row_id": _excel_safe(r.get("relationship_row_id")),
        })
    return rows


def merge_cross_sources(
    keerthana_path: Path = BETWEEN_GROUP_SOURCE_XLSX,
    v2_path: Path = DOC_LEVEL_JR_CSV,
) -> pd.DataFrame:
    """Keerthana analysis/og + v2 cross-group; drop Keerthana eHRAF stubs."""
    if not keerthana_path.is_file():
        raise FileNotFoundError(f"Keerthana source not found: {keerthana_path}")
    if not v2_path.is_file():
        raise FileNotFoundError(
            f"v2 export not found: {v2_path}\n"
            "Run: uv run python code/llm_ehraf/run.py extract && uv run python code/llm_ehraf/run.py export"
        )

    ke = pd.read_excel(keerthana_path)
    kept = keerthana_non_ehraf(ke)
    n_ehraf_dropped = sum(_is_keerthana_ehraf_row(ke.loc[i]) for i in ke.index)

    v2 = pd.read_csv(v2_path)
    v2_rows = _v2_cross_rows(v2)
    v2_df = pd.DataFrame(v2_rows)
    v2_pairs = {_pair_key(r["entity_a"], r["entity_b"]) for r in v2_rows}

    kept_filtered = []
    n_dup_skipped = 0
    for _, r in kept.iterrows():
        a, b = _clean(r.get("entity_a")), _clean(r.get("entity_b"))
        if not a or not b:
            continue
        if _pair_key(a, b) in v2_pairs:
            n_dup_skipped += 1
            continue
        kept_filtered.append(r)

    merged = pd.concat([pd.DataFrame(kept_filtered), v2_df], ignore_index=True)
    print(
        f"  Cross-group merge: Keerthana kept {len(kept_filtered)}"
        f" (dropped {n_ehraf_dropped} eHRAF, {n_dup_skipped} dup vs v2)"
        f" + v2 {len(v2_df)} = {len(merged)}"
    )
    return merged


def build_within_from_v2(v2_path: Path = DOC_LEVEL_JR_CSV) -> pd.DataFrame:
    """All v2 kinship + within_group rows in Visualization review CSV shape."""
    if not v2_path.is_file():
        raise FileNotFoundError(f"v2 export not found: {v2_path}")

    df = pd.read_csv(v2_path)
    mask = df["scope_coded"].isin(["kinship", "within_group"])
    rows: list[dict] = []
    for _, r in df[mask].iterrows():
        entity_a = _clean(r.get("entity_a"))
        entity_b = _clean(r.get("entity_b"))
        if not entity_a or not entity_b:
            continue
        rows.append({
            "relationship_id": _clean(r.get("relationship_row_id")),
            "scope_coded": "within_group",
            "region": _norm_region(_clean(r.get("region"))),
            "ethnography_group": _clean(r.get("ethnography_group")),
            "entity_a": entity_a,
            "entity_b": entity_b,
            "entity_a_canonical": entity_a,
            "entity_b_canonical": entity_b,
            "entity_a_type": _clean(r.get("entity_a_type")),
            "entity_b_type": _clean(r.get("entity_b_type")),
            "relation_type_coded": _clean(r.get("relation_type_coded")),
            "symmetry_coded": _clean(r.get("symmetry_coded")),
            "relation_labels": _clean(r.get("relation_label_raw")),
            "local_terms": _clean(r.get("local_term_raw")),
            "supporting_quote_raw": _clean(r.get("supporting_quote_raw")),
            "confidence_mean": float(r.get("confidence") or 0.0),
            "confidence_max": float(r.get("confidence") or 0.0),
            "n_assertions": 1,
            "n_source_docs": 1,
            "source_docs": _clean(r.get("doc_id")),
            "assertion_ids": _clean(r.get("relationship_row_id")),
            "joking_source": "ehraf_v2",
        })
    out = pd.DataFrame(rows)
    print(f"  Within/kinship from v2: {len(out)} rows")
    return out


def _norm_record_id(val) -> str:
    s = _clean(val)
    if not s:
        return ""
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
    except ValueError:
        pass
    return s


def _keerthana_record(rid: str, row: pd.Series) -> dict:
    joking_source = _clean(row.get("joking_source")) or "unknown"
    region = _norm_region(_clean(row.get("regions")))
    ethno = _clean(row.get("ethnography_groups"))
    notes = _clean(row.get("notes"))
    if joking_source == "analysis":
        reasoning = notes or "Keerthana structural joking analysis (Burkina Faso)."
    else:
        reasoning = notes or "Keerthana ethnography source."
    return {
        "id": rid,
        "source": "Keerthana",
        "doc_id": "",
        "source_pdf": "",
        "ethnography_group": ethno,
        "region": region,
        "entity_a": _clean(row.get("entity_a")),
        "entity_b": _clean(row.get("entity_b")),
        "entity_a_type": _clean(row.get("entity_a_type")),
        "entity_b_type": _clean(row.get("entity_b_type")),
        "scope_coded": "cross_group",
        "reasoning": reasoning,
        "notes": notes,
        "quote": _clean(row.get("original_source_text")),
        "relation_label": _clean(row.get("relation_types_coded")),
        "local_term": "",
        "symmetry": _clean(row.get("symmetry")),
        "relation_type": _clean(row.get("relation_types_coded")),
        "confidence": 0.0,
        "joking_source": joking_source,
    }


def build_jr_records(v2_path: Path = DOC_LEVEL_JR_CSV) -> dict[str, dict]:
    """Detail records for map panel — v2 rows only (Keerthana has no per-row quotes)."""
    if not v2_path.is_file():
        return {}

    df = pd.read_csv(v2_path)
    records: dict[str, dict] = {}
    for _, row in df.iterrows():
        rid = _clean(row.get("relationship_row_id"))
        if not rid:
            continue
        doc_id = _clean(row.get("doc_id"))
        records[rid] = {
            "id": rid,
            "source": "eHRAF",
            "doc_id": doc_id,
            "source_pdf": f"{doc_id.strip('/').replace('/', '_')}.pdf" if doc_id else "",
            "ethnography_group": _clean(row.get("ethnography_group")),
            "region": _clean(row.get("region")),
            "entity_a": canonicalize_entity_name(_clean(row.get("entity_a"))),
            "entity_b": canonicalize_entity_name(_clean(row.get("entity_b"))),
            "entity_a_type": _clean(row.get("entity_a_type")),
            "entity_b_type": _clean(row.get("entity_b_type")),
            "scope_coded": _clean(row.get("scope_coded")),
            "reasoning": _clean(row.get("reasoning")),
            "notes": _clean(row.get("notes")),
            "quote": _clean(row.get("supporting_quote_raw")),
            "relation_label": _clean(row.get("relation_label_raw")),
            "local_term": _clean(row.get("local_term_raw")),
            "symmetry": _clean(row.get("symmetry_coded")),
            "relation_type": _clean(row.get("relation_type_coded")),
            "confidence": float(row.get("confidence") or 0.0),
        }
    return records


def build_full_jr_records(
    cross_df: pd.DataFrame,
    v2_path: Path = DOC_LEVEL_JR_CSV,
) -> dict[str, dict]:
    """eHRAF detail records + Keerthana cross-group stubs for the map detail panel."""
    records = build_jr_records(v2_path)
    for idx, row in cross_df.iterrows():
        joking_source = _clean(row.get("joking_source")) or "unknown"
        rid = _norm_record_id(row.get("relationship_row_id"))
        if joking_source == "ehraf_v2" and rid:
            continue
        rid = rid or f"keerthana:cross:{idx}"
        records[rid] = _keerthana_record(rid, row)
    return records


def write_merged_sources(
    *,
    keerthana_path: Path = BETWEEN_GROUP_SOURCE_XLSX,
    v2_path: Path = DOC_LEVEL_JR_CSV,
    cross_out: Path = BETWEEN_GROUP_SOURCE_MERGED_XLSX,
    within_out: Path = WITHIN_GROUPS_MERGED_CSV,
    records_out: Path = JR_RECORDS_JSON,
) -> tuple[Path, Path]:
    """Write merged cross-source xlsx, within csv, and jr_records.json."""
    cross_out.parent.mkdir(parents=True, exist_ok=True)
    within_out.parent.mkdir(parents=True, exist_ok=True)

    print("Merging Keerthana + v2 eHRAF sources…")
    cross_df = merge_cross_sources(keerthana_path, v2_path)
    cross_df.to_excel(cross_out, index=False, sheet_name="between_group")
    print(f"  → {cross_out}  ({len(cross_df)} rows)")

    within_df = build_within_from_v2(v2_path)
    within_df.to_csv(within_out, index=False)
    print(f"  → {within_out}  ({len(within_df)} rows)")

    records = build_full_jr_records(cross_df, v2_path)
    with records_out.open("w", encoding="utf-8") as handle:
        json.dump(records, handle, ensure_ascii=False, indent=2)
    n_keerthana = sum(1 for r in records.values() if r.get("source") == "Keerthana")
    print(f"  → {records_out}  ({len(records)} detail records · {n_keerthana} Keerthana)")

    return cross_out, within_out


def main() -> None:
    write_merged_sources()


if __name__ == "__main__":
    main()

"""Load cross-group JR assertions from all sources with full provenance."""
from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any

import pandas as pd

_CODE = Path(__file__).resolve().parent.parent
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
_VIS = _CODE / "visualization"
if str(_VIS) not in sys.path:
    sys.path.insert(0, str(_VIS))

from polygon_registry import canonicalize_entity_name, normalize_entity_for_pair  # noqa: E402

from jr_database.config import (  # noqa: E402
    ICMID_MANUAL_XLSX,
    KEERTHANA_CROSS_XLSX,
    LLM_EHRAF_JR_CSV,
)

# Whole-cell values that mean "no cross-group partner list"
_SKIP_JOKING_LINK = frozenset({
    "",
    "nan",
    "kinship",
    "none",
    "none found",
    "not found",
    "own-ethnicity",
    "own-ethnicity, kinship",
    "kinship, own-ethnicity",
})

_SKIP_PARTNER_TOKEN = frozenset({
    "kinship",
    "own-ethnicity",
    "none",
    "none found",
    "not found",
})


def _clean(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted([normalize_entity_for_pair(a), normalize_entity_for_pair(b)]))


def _base_row(**kwargs: Any) -> dict[str, Any]:
    row = {
        "source_dataset": "",
        "entity_a_raw": "",
        "entity_b_raw": "",
        "entity_a": "",
        "entity_b": "",
        "entity_a_type": "",
        "entity_b_type": "",
        "region": "",
        "ethnography_group": "",
        "relation_type": "",
        "symmetry": "",
        "notes": "",
        "quote": "",
        "source_url": "",
        "source_citation": "",
        "doc_id": "",
        "relationship_row_id": "",
        "needs_review": 0,
    }
    row.update(kwargs)
    return row


def load_llm_ehraf(path: Path = LLM_EHRAF_JR_CSV) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"LLM eHRAF export not found: {path}")
    df = pd.read_csv(path)
    rows: list[dict[str, Any]] = []
    for _, r in df[df["scope_coded"] == "cross_group"].iterrows():
        a_raw = _clean(r.get("entity_a"))
        b_raw = _clean(r.get("entity_b"))
        a = canonicalize_entity_name(a_raw)
        b = canonicalize_entity_name(b_raw)
        if not a or not b or a == b:
            continue
        rows.append(
            _base_row(
                source_dataset="llm_ehraf",
                entity_a_raw=a_raw,
                entity_b_raw=b_raw,
                entity_a=a,
                entity_b=b,
                entity_a_type=_clean(r.get("entity_a_type")),
                entity_b_type=_clean(r.get("entity_b_type")),
                region=_clean(r.get("region")),
                ethnography_group=_clean(r.get("ethnography_group")),
                relation_type=_clean(r.get("relation_type_coded")),
                symmetry=_clean(r.get("symmetry_coded")),
                notes=_clean(r.get("reasoning")),
                quote=_clean(r.get("supporting_quote_raw")),
                doc_id=_clean(r.get("doc_id")),
                relationship_row_id=_clean(r.get("relationship_row_id")),
            )
        )
    return rows


def load_keerthana(path: Path = KEERTHANA_CROSS_XLSX) -> list[dict[str, Any]]:
    if not path.is_file():
        raise FileNotFoundError(f"Keerthana source not found: {path}")
    df = pd.read_excel(path)
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        js = _clean(r.get("joking_source")).lower()
        if js not in {"analysis", "og"}:
            continue
        a_raw = _clean(r.get("entity_a"))
        b_raw = _clean(r.get("entity_b"))
        a = canonicalize_entity_name(a_raw)
        b = canonicalize_entity_name(b_raw)
        if not a or not b or a == b:
            continue
        rows.append(
            _base_row(
                source_dataset=f"keerthana_{js}",
                entity_a_raw=a_raw,
                entity_b_raw=b_raw,
                entity_a=a,
                entity_b=b,
                entity_a_type=_clean(r.get("entity_a_type")),
                entity_b_type=_clean(r.get("entity_b_type")),
                region=_clean(r.get("regions")),
                ethnography_group=_clean(r.get("ethnography_groups")),
                relation_type=_clean(r.get("relation_types_coded")),
                symmetry=_clean(r.get("symmetry")),
                notes=_clean(r.get("notes")),
                quote=_clean(r.get("original_source_text")),
            )
        )
    return rows


def _parse_joking_partners(val: Any) -> list[str]:
    """Parse Sheet2 column F: comma-separated JR partner group names."""
    s = _clean(val)
    if not s or s.casefold() in _SKIP_JOKING_LINK:
        return []
    low = s.casefold()
    if "http" in low or "article" in low or "access" in low:
        return []

    out: list[str] = []
    seen: set[str] = set()
    for part in re.split(r"[,;/]", s):
        p = part.strip()
        pl = p.casefold()
        if not p or pl in _SKIP_JOKING_LINK or pl in _SKIP_PARTNER_TOKEN:
            continue
        if pl in seen:
            continue
        seen.add(pl)
        out.append(p)
    return out


def load_icmid_manual(path: Path = ICMID_MANUAL_XLSX) -> list[dict[str, Any]]:
    """Load ICMID manual Africa workbook.

    - Sheet1: small confirmed pairs (Ethnic Group ↔ Relation With)
    - Sheet2: main coding — each row is a Murdock homeland; column F
      ``Joking link`` lists comma-separated groups with cross-group JR.
      Partners need not already be in the Murdock column (extra groups).
    - Sheet3: ignored
    """
    if not path.is_file():
        raise FileNotFoundError(f"ICMID manual workbook not found: {path}")
    rows: list[dict[str, Any]] = []

    s1 = pd.read_excel(path, sheet_name="Sheet1")
    for _, r in s1.iterrows():
        a_raw = _clean(r.get("Ethnic Group"))
        b_raw = _clean(r.get("Relation With"))
        a = canonicalize_entity_name(a_raw)
        b = canonicalize_entity_name(b_raw)
        if not a or not b or a == b:
            continue
        rows.append(
            _base_row(
                source_dataset="icmid_sheet1",
                entity_a_raw=a_raw,
                entity_b_raw=b_raw,
                entity_a=a,
                entity_b=b,
                notes=_clean(r.get("Comments")),
                source_url=_clean(r.get("Source")),
                source_citation=_clean(r.get("Source")),
            )
        )

    s2 = pd.read_excel(path, sheet_name="Sheet2")
    f_col = "Joking link" if "Joking link" in s2.columns else s2.columns[5]
    for _, r in s2.iterrows():
        a_raw = _clean(r.get("Ethnic Group"))
        if not a_raw:
            continue
        partners = _parse_joking_partners(r.get(f_col))
        if not partners:
            continue
        a = canonicalize_entity_name(a_raw)
        region = _clean(r.get("Region"))
        url = _clean(r.get("Source_URL")) or _clean(r.get("Sources"))
        cite = _clean(r.get("Source_Full_Citation"))
        quote = _clean(r.get("Source_Quote"))
        notes = _clean(r.get("Notes"))
        for b_raw in partners:
            b = canonicalize_entity_name(b_raw)
            if not a or not b or a == b:
                continue
            rows.append(
                _base_row(
                    source_dataset="icmid_sheet2",
                    entity_a_raw=a_raw,
                    entity_b_raw=b_raw,
                    entity_a=a,
                    entity_b=b,
                    region=region,
                    notes=notes,
                    quote=quote,
                    source_url=url,
                    source_citation=cite,
                    needs_review=0,
                )
            )
    return rows


def load_all_cross_assertions() -> pd.DataFrame:
    rows = load_llm_ehraf() + load_keerthana() + load_icmid_manual()
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["pair_key"] = [
        "|".join(pair_key(a, b)) for a, b in zip(df["entity_a"], df["entity_b"])
    ]
    return df

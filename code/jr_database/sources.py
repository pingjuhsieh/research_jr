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
        "source_page": "",
        "doc_id": "",
        "relationship_row_id": "",
        "needs_review": 0,
    }
    row.update(kwargs)
    return row


def _read_llm_csv(path: Path) -> pd.DataFrame:
    """Read LLM export; tolerate Numbers semicolon / broken-quote exports."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    header = raw.splitlines()[0] if raw else ""
    sep = ";" if header.count(";") > header.count(",") else ","
    df = pd.read_csv(path, sep=sep, engine="python", on_bad_lines="warn")
    if len(df.columns) == 1 and ";" in str(df.columns[0]):
        df = pd.read_csv(path, sep=";", engine="python", on_bad_lines="warn")
    # Rewrite a clean comma CSV when the on-disk file was ';' separated.
    if sep == ";" or (";" in header and header.count(";") >= 10):
        df.to_csv(path, index=False)
    return df


def load_llm_ehraf(path: Path = LLM_EHRAF_JR_CSV) -> list[dict[str, Any]]:
    """Load LLM eHRAF assertions, keeping only cross-group scope.

    Source is ``llm_ehraf_joking_relationships.csv`` (all scopes). Kinship /
    within_group rows are ignored here — this pipeline is cross-group only.
    Also accepts legacy ``between_groups`` as an alias of cross_group.
    """
    if not path.is_file():
        raise FileNotFoundError(f"LLM eHRAF export not found: {path}")
    df = _read_llm_csv(path)
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        scope = _clean(r.get("scope_coded")).casefold().replace("-", "_")
        if scope not in {"cross_group", "between_groups"}:
            continue
        a_raw = _clean(r.get("entity_a")) or _clean(r.get("entity_a_canonical"))
        b_raw = _clean(r.get("entity_b")) or _clean(r.get("entity_b_canonical"))
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
                notes=_clean(r.get("reasoning")) or _clean(r.get("notes")),
                quote=_clean(r.get("supporting_quote_raw")),
                doc_id=_clean(r.get("doc_id")) or _clean(r.get("source_docs")),
                relationship_row_id=(
                    _clean(r.get("relationship_row_id"))
                    or _clean(r.get("relationship_id"))
                ),
            )
        )
    return rows


def load_keerthana(path: Path = KEERTHANA_CROSS_XLSX) -> list[dict[str, Any]]:
    """Load Keerthana cross-group pairs.

    Only ``joking_source=analysis`` is kept. ``og`` rows were dropped as
    duplicates of the newer llm_ehraf stream.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Keerthana source not found: {path}")
    df = pd.read_excel(path)
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        js = _clean(r.get("joking_source")).lower()
        if js != "analysis":
            continue
        a_raw = _clean(r.get("entity_a"))
        b_raw = _clean(r.get("entity_b"))
        a = canonicalize_entity_name(a_raw)
        b = canonicalize_entity_name(b_raw)
        if not a or not b or a == b:
            continue
        rows.append(
            _base_row(
                source_dataset="keerthana_analysis",
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


def load_icmid_jr_pair(path: Path = ICMID_MANUAL_XLSX) -> list[dict[str, Any]]:
    """Load curated undirected pairs from sheet ``JR_pair`` (preferred over Sheet2)."""
    if not path.is_file():
        return []
    try:
        df = pd.read_excel(path, sheet_name="JR_pair")
    except ValueError:
        return []
    df.columns = [str(c).strip() for c in df.columns]
    rows: list[dict[str, Any]] = []
    for _, r in df.iterrows():
        a_raw = _clean(r.get("entity_a"))
        b_raw = _clean(r.get("entity_b"))
        a = canonicalize_entity_name(a_raw)
        b = canonicalize_entity_name(b_raw)
        if not a or not b or a.casefold() == b.casefold():
            continue
        notes = _clean(r.get("Notes"))
        rows.append(
            _base_row(
                source_dataset="icmid_jr_pair",
                entity_a_raw=a_raw,
                entity_b_raw=b_raw,
                entity_a=a,
                entity_b=b,
                region=_clean(r.get("Region")),
                notes=notes,
                quote=_clean(r.get("Source_Quote")),
                source_url=_clean(r.get("Source_URL")) or _clean(r.get("Sources")),
                source_citation=_clean(r.get("Source_Full_Citation")),
                source_page=_clean(r.get("Source_Page")),
                doc_id=_clean(r.get("Source_File")),
                needs_review=1 if _clean(r.get("source_review")) else 0,
            )
        )
    return rows


def load_icmid_manual(path: Path = ICMID_MANUAL_XLSX) -> list[dict[str, Any]]:
    """Load ICMID manual Africa workbook.

    - Sheet1: small confirmed pairs (Ethnic Group ↔ Relation With)
    - ``JR_pair`` (preferred): curated one-row-per-undirected-pair with sources
    - Sheet2 fallback: only if ``JR_pair`` is missing/empty
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

    jr_pair_rows = load_icmid_jr_pair(path)
    if jr_pair_rows:
        rows.extend(jr_pair_rows)
        return rows

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
        page = _clean(r.get("Source_Page"))
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
                    source_page=page,
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

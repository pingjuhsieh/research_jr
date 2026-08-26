"""Ethnic entity index — single source of truth (ethnic_entity_index.xlsx).

Edit the xlsx directly to set polygon_source, polygon_id, parent_ethnic_group.
prepare.py adds missing entity stubs only — it never guesses GIS matches.
Unmatched rows → output/visualization/unmatched_homelands.xlsx for manual review.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    BETWEEN_GROUP_SOURCE_XLSX,
    ETHNIC_ENTITY_INDEX_XLSX,
    KEERTHANA_ETHNICS_XLSX,
    WITHIN_GROUPS_CSV,
)
from entity_homeland import VALID_POLYGON_SOURCES, index_polygon_trusted, infer_parent_group

# Entity types that belong in the ethnic index (homeland / alias concordance).
INDEXABLE_ENTITY_TYPES: frozenset[str] = frozenset({
    "ethnic_group",
    "subgroup",
    "clan",
    "lineage",
    "regional_group",
    "tribe",
    "patronym",
})

# JR role endpoints — stay in JR tables only, not in the index.
NON_INDEXABLE_ENTITY_TYPES: frozenset[str] = frozenset({
    "person",
    "kin_role",
    "kin",
    "place",
    "class",
    "group",       # generic role ("a commoner"), not an ethnic group name
})

INDEX_COLUMNS = [
    "raw_value",           # PK — name as it appears in JR data
    "canonical_name",
    "entity_type",         # ethnic_group, clan, kin_role, person, …
    "polygon_source",      # murdock | greg | geopr | joshua | unresolved
    "polygon_id",          # polygon name in that GIS system
    "parent_ethnic_group", # optional display helper; use polygon_id for grouping
    "region",              # WesternAfrica, EasternAfrica, …
    "country",
    "resolve_source",      # where the mapping came from (wiki URL, paper, …)
    "coder",               # who filled the mapping
    "notes",
]

_ILLEGAL_XL_CHARS = re.compile(r"[\x00-\x1f\x7f-\x9f]")

# Generic kin-role phrases mis-tagged as clan/lineage in source JR data.
_KIN_ROLE_NAME = re.compile(
    r"\b(his|her|my|your)\s+(wife|husband|mother|father|brother|sister)\b|"
    r"mother'?s\s+brother|wife'?s\s+clan|father'?s\s+sister|a\s+commoner",
    re.IGNORECASE,
)


def _sanitize_for_excel(val: Any) -> Any:
    if isinstance(val, str):
        return _ILLEGAL_XL_CHARS.sub("", val)
    return val


_LEGACY_COLUMN_MAP = {
    "type": "entity_type",
    "homeland_source": "polygon_source",
    "maps_to_ethnic_group": "parent_ethnic_group",
    "murdock_shapefile": "polygon_id",
    "Source": "polygon_source",
    "MurdockShapefile": "polygon_id",
}


def _clean(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    if s.lower() == "nan":
        return ""
    return _sanitize_for_excel(s)


def normalize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Rename legacy columns and ensure schema."""
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    for old, new in _LEGACY_COLUMN_MAP.items():
        if old in out.columns and new not in out.columns:
            out = out.rename(columns={old: new})
    for col in INDEX_COLUMNS:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str).replace("nan", "")
    out["raw_value"] = out["raw_value"].map(_clean)
    out = out[out["raw_value"] != ""].copy()
    out["entity_type"] = out["entity_type"].map(lambda v: _norm_entity_type(v) if _clean(v) else "")
    # Fill parent from parenthetical name when blank (display helper only)
    for i, row in out.iterrows():
        if not _clean(row.get("parent_ethnic_group")):
            out.at[i, "parent_ethnic_group"] = infer_parent_group(_clean(row["raw_value"]))
        if not _clean(row.get("canonical_name")):
            out.at[i, "canonical_name"] = _clean(row["raw_value"])
    out = out.drop_duplicates(subset=["raw_value"], keep="last")
    return out[INDEX_COLUMNS]


def _norm_entity_type(etype: str) -> str:
    return _clean(etype).lower().replace(" ", "_").replace("-", "_")


def looks_like_kin_role_label(name: str) -> bool:
    """True for generic kin references, not real clan/ethnic names."""
    return bool(_KIN_ROLE_NAME.search(_clean(name)))


def is_indexable_entity_type(etype: str) -> bool:
    """True for ethnic groups, clans, subgroups — not kin/person roles."""
    norm = _norm_entity_type(etype)
    if not norm:
        return False
    if norm in NON_INDEXABLE_ENTITY_TYPES:
        return False
    return norm in INDEXABLE_ENTITY_TYPES


def _should_keep_index_row(row: pd.Series | dict) -> bool:
    """Drop auto-added junk; keep resolved homelands and indexable entities."""
    raw = _clean(row.get("raw_value", ""))
    if looks_like_kin_role_label(raw):
        return False
    et = _norm_entity_type(row.get("entity_type", ""))
    if et in NON_INDEXABLE_ENTITY_TYPES:
        return False
    if compute_homeland_found(row):
        return True
    if et and is_indexable_entity_type(et):
        return True
    # empty type + no homeland → auto stub (e.g. kin/person name wrongly added)
    return False


def prune_index_stubs(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Remove rows that don't belong in the ethnic entity index."""
    before = len(df)
    kept = df[df.apply(_should_keep_index_row, axis=1)].copy()
    return normalize_dataframe(kept), before - len(kept)


def homeland_key_from_row(row: pd.Series | dict) -> str:
    """Stable key: source:POLYGON_ID, parent:GROUP, or entity:NAME."""
    src = _clean(row.get("polygon_source", "")).lower()
    pid = _clean(row.get("polygon_id", ""))
    parent = _clean(row.get("parent_ethnic_group", ""))
    raw = _clean(row.get("raw_value", ""))
    if src in VALID_POLYGON_SOURCES and pid:
        return f"{src}:{pid.upper()}"
    if parent:
        return f"parent:{parent.upper()}"
    canon = _clean(row.get("canonical_name", "")) or raw
    return f"entity:{canon.upper()}"


def group_map_key_from_row(row: pd.Series | dict) -> str:
    """Canonical polygon_id (UPPERCASE) for map grouping and JR lookup."""
    pid = _clean(row.get("polygon_id", "")).upper()
    if pid:
        return pid
    parent = _clean(row.get("parent_ethnic_group", "")).upper()
    if parent:
        return parent
    return (_clean(row.get("canonical_name", "")) or _clean(row.get("raw_value", ""))).upper()


def compute_homeland_found(row: pd.Series | dict) -> bool:
    src = _clean(row.get("polygon_source", "")).lower()
    pid = _clean(row.get("polygon_id", ""))
    return src in VALID_POLYGON_SOURCES and bool(pid)


def load_index(path: Path = ETHNIC_ENTITY_INDEX_XLSX) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame(columns=INDEX_COLUMNS)
    return normalize_dataframe(pd.read_excel(path))


def save_index(df: pd.DataFrame, path: Path = ETHNIC_ENTITY_INDEX_XLSX) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = normalize_dataframe(df)
    out["homeland_found"] = out.apply(compute_homeland_found, axis=1)
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(_sanitize_for_excel)
    out.to_excel(path, index=False, sheet_name="entity_index")


def _lookup_key(name: str) -> str:
    """Case-insensitive index key (NGONI and Ngoni are the same)."""
    return _clean(name).casefold()


def build_lookup(df: pd.DataFrame) -> dict[str, pd.Series]:
    """raw_value and canonical_name → index row (case-insensitive).

    When keys collide, prefer a row that already maps to a homeland polygon.
    Otherwise an unresolved row like ``Wasili (Arabs)`` with
    ``canonical_name=Wasili`` can shadow a later filled ``Wasili → SHUWA``.
    """
    lookup: dict[str, pd.Series] = {}
    for _, row in df.iterrows():
        for key in {_lookup_key(row["raw_value"]), _lookup_key(row["canonical_name"])}:
            if not key:
                continue
            existing = lookup.get(key)
            if existing is None:
                lookup[key] = row
                continue
            if not compute_homeland_found(existing) and compute_homeland_found(row):
                lookup[key] = row
    return lookup


def lookup_row(lookup: dict[str, pd.Series], name: str) -> pd.Series | None:
    key = _lookup_key(name)
    if not key:
        return None
    row = lookup.get(key)
    if row is not None and compute_homeland_found(row):
        return row

    # Parenthetical fallback: "Azande (Agiti)" / "Wasili (Arabs)" → outer/inner
    # Also try when the exact key hits an *unresolved* row, so a filled
    # "Wasili → SHUWA" can still serve "Wasili (Arabs)".
    raw = _clean(name)
    m = re.search(r"\((.+?)\)", raw)
    for candidate in (m.group(1).strip() if m else None, re.sub(r"\s*\(.*?\)", "", raw).strip()):
        ck = _lookup_key(candidate or "")
        if not ck or ck == key:
            continue
        crow = lookup.get(ck)
        if crow is not None and compute_homeland_found(crow):
            return crow

    if row is not None:
        return row
    for candidate in (m.group(1).strip() if m else None, re.sub(r"\s*\(.*?\)", "", raw).strip()):
        ck = _lookup_key(candidate or "")
        if ck and ck in lookup:
            return lookup[ck]
    return None


def annotate_entity(
    lookup: dict[str, pd.Series],
    name: str,
    parent_hint: str = "",
) -> dict[str, str]:
    """Homeland fields for one entity, read from the index (or parent fallback)."""
    empty = {
        "homeland_status": "missing",
        "polygon_source": "",
        "polygon_id": "",
        "parent_group": "",
        "region": "",
        "homeland_key": "",
        "group_map_key": "",
    }
    if not name:
        return empty
    row = lookup_row(lookup, name)
    if row is None and parent_hint:
        row = lookup_row(lookup, parent_hint)
    if row is None:
        return {**empty, "homeland_status": "not_in_index"}
    found = compute_homeland_found(row)
    return {
        "homeland_status": _clean(row["polygon_source"]) if found else "not_found",
        "polygon_source": _clean(row["polygon_source"]),
        "polygon_id": _clean(row["polygon_id"]),
        "parent_group": _clean(row["parent_ethnic_group"]),
        "region": _clean(row["region"]),
        "homeland_key": homeland_key_from_row(row),
        "group_map_key": group_map_key_from_row(row),
    }


def bootstrap_from_keerthana(path: Path = KEERTHANA_ETHNICS_XLSX) -> pd.DataFrame:
    """One-time import from Keerthana ethnics workbook → new index schema."""
    source_map = {
        "murdock": "murdock",
        "greg": "greg",
        "geopr": "geopr",
        "geoepr": "geopr",
        "joshuaproject": "joshua",
        "joshua project": "joshua",
        "joshua": "joshua",
    }
    raw = pd.read_excel(path)
    rows = []
    for _, r in raw.iterrows():
        raw_value = _clean(r.get("raw_value")) or _clean(r.get("canonical_name"))
        if not raw_value:
            continue
        canonical = _clean(r.get("canonical_name")) or raw_value
        maps_to = _clean(r.get("maps_to_ethnic_group"))
        keerthana_src = source_map.get(_clean(r.get("Source")).lower(), "unresolved")
        murdock_sheet = _clean(r.get("MurdockShapefile"))
        polygon_id = murdock_sheet.split(",")[0].strip() if murdock_sheet else ""
        polygon_source = keerthana_src
        if polygon_source == "unresolved" and polygon_id:
            polygon_source = "murdock"

        rows.append({
            "raw_value": raw_value,
            "canonical_name": canonical,
            "entity_type": _clean(r.get("type")),
            "polygon_source": polygon_source,
            "polygon_id": polygon_id,
            "parent_ethnic_group": maps_to or infer_parent_group(raw_value),
            "region": _clean(r.get("region")),
            "country": _clean(r.get("country")),
            "notes": _clean(r.get("notes"))[:300],
        })
    return normalize_dataframe(pd.DataFrame(rows))


def _register_candidate(
    candidates: dict[str, dict],
    name: str,
    entity_type: str,
    parent_ethnic_group: str = "",
    ethnography: str = "",
) -> None:
    """Add one index candidate if the entity type warrants an index row."""
    name = _clean(name)
    if not name or looks_like_kin_role_label(name):
        return
    et = _norm_entity_type(entity_type)
    # ethnography_group labels are always ethnic groups
    if not et and ethnography and name == _clean(ethnography):
        et = "ethnic_group"
    if not is_indexable_entity_type(et):
        return
    parent = _clean(parent_ethnic_group) or infer_parent_group(name)
    prev = candidates.get(name)
    if prev is None:
        candidates[name] = {
            "entity_type": et,
            "parent_ethnic_group": parent,
        }
        return
    # Prefer richer type / parent info
    if not prev.get("parent_ethnic_group") and parent:
        prev["parent_ethnic_group"] = parent


def collect_index_candidates(
    joking_path: Path | None = None,
    within_csv: Path = WITHIN_GROUPS_CSV,
) -> dict[str, dict]:
    """Names that should appear in the ethnic index (groups/clans only, not kin/person)."""
    candidates: dict[str, dict] = {}
    jp = joking_path or BETWEEN_GROUP_SOURCE_XLSX
    if jp.is_file():
        df = pd.read_excel(jp) if jp.suffix == ".xlsx" else pd.read_csv(jp)
        ethno_col = "ethnography_groups" if "ethnography_groups" in df.columns else "ethnography_group"
        for _, row in df.iterrows():
            ethno = _clean(row.get(ethno_col, ""))
            for prefix in ("entity_a", "entity_b"):
                _register_candidate(
                    candidates,
                    _clean(row.get(prefix, "")),
                    _clean(row.get(f"{prefix}_type", "")),
                    parent_ethnic_group=ethno,
                )
    if within_csv.is_file():
        df = pd.read_csv(within_csv)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
        for _, row in df.iterrows():
            ethno = _clean(row.get("ethnography_group", ""))
            if ethno:
                _register_candidate(candidates, ethno, "ethnic_group")
            for ep in ("entity_a", "entity_b"):
                name = _clean(row.get(f"{ep}_canonical", row.get(ep, "")))
                et = _clean(row.get(f"{ep}_type", ""))
                _register_candidate(candidates, name, et, parent_ethnic_group=ethno)
    return candidates


def collect_entity_names(
    joking_path: Path | None = None,
    within_csv: Path = WITHIN_GROUPS_CSV,
) -> set[str]:
    """Backward-compatible wrapper — indexable names only."""
    return set(collect_index_candidates(joking_path, within_csv).keys())


def sync_new_entities(
    df: pd.DataFrame,
    candidates: dict[str, dict] | set[str],
) -> tuple[pd.DataFrame, int]:
    """Append stub rows for indexable entities not yet in the index."""
    if isinstance(candidates, set):
        candidates = {n: {"entity_type": "", "parent_ethnic_group": ""} for n in candidates}

    existing = set(df["raw_value"].map(_clean))
    added = 0
    new_rows: list[dict] = []
    for name in sorted(candidates.keys()):
        if name in existing:
            continue
        meta = candidates[name]
        et = _norm_entity_type(meta.get("entity_type", ""))
        parent = _clean(meta.get("parent_ethnic_group", "")) or infer_parent_group(name)
        new_rows.append({
            "raw_value": name,
            "canonical_name": infer_parent_group(name) or name,
            "entity_type": et,
            "polygon_source": "unresolved",
            "polygon_id": "",
            "parent_ethnic_group": parent,
            "region": "",
            "country": "",
            "notes": "",
        })
        added += 1
    if not new_rows:
        return df, 0
    combined = pd.concat([df, pd.DataFrame(new_rows)], ignore_index=True)
    return normalize_dataframe(combined), added


UNMATCHED_COLUMNS = [
    "raw_value",
    "canonical_name",
    "entity_type",
    "parent_ethnic_group",
    "polygon_source",
    "polygon_id",
    "region",
    "country",
    "issue",
    "suggested_action",
]


def scrub_legacy_auto_guesses(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Clear index rows left from old auto-fill where raw_value ≠ polygon_id.

    E.g. Po → geopr:Poles. Sub-clans (parent set or parentheses) are kept.
    """
    out = df.copy()
    scrubbed = 0
    for i, row in out.iterrows():
        raw = _clean(row.get("raw_value", ""))
        src = _clean(row.get("polygon_source", "")).lower()
        pid = _clean(row.get("polygon_id", ""))
        if not raw or src in ("", "unresolved") or not pid:
            continue
        if index_polygon_trusted(raw, row):
            continue
        note = _clean(row.get("notes", ""))
        out.at[i, "polygon_source"] = "unresolved"
        out.at[i, "polygon_id"] = ""
        msg = "scrubbed: legacy auto-guess (name≠polygon_id)"
        out.at[i, "notes"] = f"{note}; {msg}".strip("; ") if note else msg
        scrubbed += 1
    return out, scrubbed


def export_unmatched_homelands(df: pd.DataFrame, resolver) -> pd.DataFrame:
    """List index rows that still need manual polygon_source / polygon_id.

    Does not modify the index — edit ethnic_entity_index.xlsx by hand, then re-run prepare.py data.
    """
    rows: list[dict] = []
    for _, row in df.iterrows():
        raw = _clean(row.get("raw_value", ""))
        if not raw:
            continue
        ok, issue = resolver.verify_index_row(row)
        if ok:
            continue
        if issue == "missing_or_invalid_polygon_source":
            action = "Set polygon_source to murdock | greg | geopr | joshua"
        elif issue == "missing_polygon_id":
            action = "Set polygon_id to the exact GIS layer name (case may differ)"
        else:
            action = (
                f"polygon_id not found in {_clean(row.get('polygon_source'))} — "
                "check spelling or pick another layer"
            )
        rows.append({
            "raw_value": raw,
            "canonical_name": _clean(row.get("canonical_name")),
            "entity_type": _clean(row.get("entity_type")),
            "parent_ethnic_group": _clean(row.get("parent_ethnic_group")),
            "polygon_source": _clean(row.get("polygon_source")),
            "polygon_id": _clean(row.get("polygon_id")),
            "region": _clean(row.get("region")),
            "country": _clean(row.get("country")),
            "issue": issue,
            "suggested_action": action,
        })
    out = pd.DataFrame(rows, columns=UNMATCHED_COLUMNS)
    if not out.empty:
        out = out.sort_values(["issue", "raw_value"]).reset_index(drop=True)
    return out

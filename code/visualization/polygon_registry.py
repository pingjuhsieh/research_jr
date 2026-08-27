"""Polygon group registry — manually maintained name → polygon_id mapping.

`polygon_group_registry.xlsx` is the canonical list of ethnic groups used for JR
grouping. Each row is one ethnic group, keyed by `polygon_id`.

Design (see README):
  - Murdock is the preferred polygon source when it exists for a polygon_id.
  - GREG / GeoEPR / Joshua are fallbacks for groups with no Murdock polygon.
  - Same polygon_id in the entity index under multiple sources → one registry row,
    always Murdock (no duplicate GREG row).
  - Same ethnicity under different names (e.g. Fulani vs Fulbe) → separate rows
    until you merge manually via the aliases column. No automatic synonym rules.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import pandas as pd

from config import ETHNIC_ENTITY_INDEX_XLSX, POLYGON_GROUP_REGISTRY_XLSX, WITHIN_GROUP_XLSX
from jr_tables import load_within_group
from entity_homeland import VALID_POLYGON_SOURCES, index_polygon_trusted
from entity_index import _clean, _sanitize_for_excel, lookup_row

# Sub-clan / lineage types belong in ethnic_entity_index, not registry aliases.
_SUBGROUP_ENTITY_TYPES = frozenset({
    "subgroup", "clan", "lineage", "patronym", "regional_group", "tribe",
})

REGISTRY_COLUMNS = [
    "polygon_id",       # canonical unique ID, e.g. FULBE (PK)
    "polygon_source",   # murdock | greg | geopr | joshua — preferred map layer
    "display_name",     # optional label on the map
    "aliases",          # comma-separated alternate names, e.g. Fulani, Peul
    "region",
    "notes",
]

SOURCE_PRIORITY: dict[str, int] = {
    "murdock": 0,
    "greg": 1,
    "geopr": 2,
    "joshua": 3,
}


def _split_aliases(val: Any) -> list[str]:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return []
    return [_clean(a) for a in str(val).split(",") if _clean(a)]


def lookup_name_variants(name: str) -> list[str]:
    """Uppercase keys to try against the registry alias map."""
    n = _clean(name).upper()
    if not n:
        return []
    variants = [n]
    if n.startswith("THE "):
        variants.append(n[4:].strip())
    return [v for v in variants if v]


def canonicalize_entity_name(name: str) -> str:
    """Preferred display name for known entity spelling variants."""
    s = _clean(name)
    if not s:
        return ""
    key = re.sub(r"^the\s+", "", s, flags=re.I).casefold()
    display_aliases = {
        "wa-sukuma": "Sukuma",
        "sukuma": "Sukuma",
    }
    if key in display_aliases:
        return display_aliases[key]
    stripped = re.sub(r"^the\s+", "", s, flags=re.I)
    return stripped if stripped else s


def normalize_entity_for_pair(name: str) -> str:
    """Casefold key for JR pair dedup and detail-panel linking."""
    return canonicalize_entity_name(name).casefold()


def normalize_registry(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip() for c in out.columns]
    for col in REGISTRY_COLUMNS:
        if col not in out.columns:
            out[col] = ""
        out[col] = out[col].fillna("").astype(str).replace("nan", "")
    out["polygon_id"] = out["polygon_id"].map(lambda v: _clean(v).upper())
    out = out[out["polygon_id"] != ""].copy()
    if out["display_name"].eq("").all() and not out.empty:
        out["display_name"] = out["polygon_id"].str.title()
    out = out.drop_duplicates(subset=["polygon_id"], keep="last")
    return out[REGISTRY_COLUMNS]


def load_registry(path: Path = POLYGON_GROUP_REGISTRY_XLSX) -> pd.DataFrame:
    if not path.is_file():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)
    return normalize_registry(pd.read_excel(path))


def save_registry(df: pd.DataFrame, path: Path = POLYGON_GROUP_REGISTRY_XLSX) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = normalize_registry(df)
    for col in out.columns:
        if out[col].dtype == object:
            out[col] = out[col].map(_sanitize_for_excel)
    out.to_excel(path, index=False, sheet_name="polygon_groups")


def build_manual_alias_map(registry_df: pd.DataFrame) -> dict[str, str]:
    """Map manually entered names → polygon_id: polygon_id + aliases column only.

    display_name is NOT used for matching — avoids bootstrapped names like
    Albanians / Poles resolving without explicit user aliases.
    """
    mapping: dict[str, str] = {}
    for _, row in registry_df.iterrows():
        pid = _clean(row["polygon_id"]).upper()
        if not pid:
            continue
        mapping[pid] = pid
        for alias in _split_aliases(row.get("aliases", "")):
            mapping[alias.upper()] = pid
    return mapping


def build_name_to_polygon_map(registry_df: pd.DataFrame) -> dict[str, str]:
    """Alias map for JR grouping — same as manual map (no display_name)."""
    return build_manual_alias_map(registry_df)


def build_registry_by_id(registry_df: pd.DataFrame) -> dict[str, pd.Series]:
    """polygon_id (UPPER) → registry row."""
    out: dict[str, pd.Series] = {}
    for _, row in registry_df.iterrows():
        pid = _clean(row.get("polygon_id", "")).upper()
        if pid:
            out[pid] = row
    return out


def gis_labels_for_registry_row(row: pd.Series | dict) -> list[str]:
    """Exact GIS names to try for a registry row's polygon_source."""
    pid = _clean(row.get("polygon_id", ""))
    disp = _clean(row.get("display_name", ""))
    labels: list[str] = []
    for candidate in (disp, pid, pid.title() if pid else ""):
        if candidate and candidate not in labels:
            labels.append(candidate)
    return labels


def resolve_polygon_id(
    name: str,
    registry_map: dict[str, str],
    index_lookup: dict | None = None,
) -> str:
    """Resolve a name to canonical polygon_id.

    Registry (incl. manual aliases) is checked before entity_index so e.g.
    Fulani → FULBE when aliases lists Fulani, even if the index has a separate
    joshua:Fulani row.
    """
    if not name:
        return ""

    for n in lookup_name_variants(name):
        if n in registry_map:
            return registry_map[n]

    outer = re.sub(r"\s*\(.*?\)", "", name).strip().upper()
    for n in lookup_name_variants(outer):
        if n in registry_map:
            return registry_map[n]

    if index_lookup is not None:
        row = lookup_row(index_lookup, name)
        if row is not None:
            pid = _clean(row.get("polygon_id", "")).upper()
            if pid and index_polygon_trusted(name, row):
                return registry_map.get(pid, pid)
            parent = _clean(row.get("parent_ethnic_group", "")).upper()
            if parent:
                if parent in registry_map:
                    return registry_map[parent]
                return parent

    return n


def _is_subgroup_index_row(row: pd.Series, polygon_id: str = "") -> bool:
    """True when this entity_index row is a sub-clan, not a registry alias."""
    parent = _clean(row.get("parent_ethnic_group", ""))
    if parent:
        return True
    et = _clean(row.get("entity_type", "")).lower().replace(" ", "_").replace("-", "_")
    if et in _SUBGROUP_ENTITY_TYPES:
        return True
    raw = _clean(row.get("raw_value", ""))
    if "(" in raw:
        outer = re.sub(r"\s*\(.*?\)", "", raw).strip()
        pid = _clean(polygon_id).upper() or _clean(row.get("polygon_id", "")).upper()
        if outer and pid and outer.upper() == pid:
            return True
    return False


def _should_add_registry_alias(row: pd.Series, polygon_id: str) -> bool:
    """Only true alternate ethnic-group names — not sub-clans in entity_index."""
    raw = _clean(row.get("raw_value", ""))
    if not raw or raw.upper() == _clean(polygon_id).upper():
        return False
    if _is_subgroup_index_row(row, polygon_id):
        return False
    return True


def scrub_subgroup_aliases(
    registry_df: pd.DataFrame,
    index_df: pd.DataFrame,
) -> pd.DataFrame:
    """Remove entity_index sub-clan names mistakenly listed as registry aliases."""
    subgroup_names: set[str] = set()
    for _, row in index_df.iterrows():
        if _is_subgroup_index_row(row):
            subgroup_names.add(_clean(row.get("raw_value", "")))

    out = registry_df.copy()
    for i, row in out.iterrows():
        kept = [a for a in _split_aliases(row.get("aliases", "")) if a not in subgroup_names]
        out.at[i, "aliases"] = ", ".join(kept)
    return normalize_registry(out)


def _pick_source(current: str, candidate: str) -> str:
    cur = _clean(current).lower()
    cand = _clean(candidate).lower()
    if cand not in VALID_POLYGON_SOURCES:
        return cur
    if cur not in VALID_POLYGON_SOURCES:
        return cand
    return cand if SOURCE_PRIORITY.get(cand, 99) < SOURCE_PRIORITY.get(cur, 99) else cur


def bootstrap_from_entity_index(
    index_path: Path = ETHNIC_ENTITY_INDEX_XLSX,
) -> pd.DataFrame:
    """Seed registry from ethnic_entity_index.xlsx.

  Murdock rows are processed first. GREG / GeoEPR / Joshua rows are only added
  when that polygon_id is not already covered by Murdock — so the registry never
  duplicates a group as both murdock and greg.

  Different polygon_ids (e.g. FULANI joshua vs Fulbe greg) stay as separate rows;
  merge them manually in aliases. Bootstrap only copies distinct polygon_ids —
  never raw_value names.
    """
    if not index_path.is_file():
        return pd.DataFrame(columns=REGISTRY_COLUMNS)

    index_df = pd.read_excel(index_path)
    groups: dict[str, dict] = {}

    def _ingest(row: pd.Series) -> None:
        pid = _clean(row.get("polygon_id", "")).upper()
        if not pid:
            return
        src = _clean(row.get("polygon_source", "")).lower()
        if src not in VALID_POLYGON_SOURCES:
            return
        region = _clean(row.get("region", ""))

        if pid not in groups:
            groups[pid] = {
                "polygon_id": pid,
                "polygon_source": src,
                "display_name": pid.title(),
                "aliases": set(),
                "region": region,
                "notes": "bootstrapped from entity index polygon_ids",
            }
        g = groups[pid]
        g["polygon_source"] = _pick_source(g["polygon_source"], src)
        if region and not g["region"]:
            g["region"] = region
        # aliases are never bootstrapped — add manually in the xlsx

    # Pass 1: Murdock — canonical polygon coverage
    for _, row in index_df.iterrows():
        if _clean(row.get("polygon_source", "")).lower() == "murdock":
            _ingest(row)

    # Pass 2: greg only — geopr/joshua are never bootstrapped (manual registry only)
    for _, row in index_df.iterrows():
        src = _clean(row.get("polygon_source", "")).lower()
        if src != "greg":
            continue
        pid = _clean(row.get("polygon_id", "")).upper()
        if pid and pid in groups and groups[pid]["polygon_source"] == "murdock":
            continue
        _ingest(row)

    rows = []
    for g in sorted(groups.values(), key=lambda x: x["polygon_id"]):
        rows.append({
            "polygon_id": g["polygon_id"],
            "polygon_source": g["polygon_source"],
            "display_name": g["display_name"],
            "aliases": ", ".join(sorted(g["aliases"])),
            "region": g["region"],
            "notes": g["notes"],
        })
    return normalize_registry(pd.DataFrame(rows))


def remove_auto_bootstrapped_registry_rows(registry_df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop registry rows auto-created from entity index (geopr/joshua noise).

    Keeps manually maintained rows (no bootstrapped note, or murdock/greg).
    """
    if registry_df.empty:
        return registry_df, 0
    before = len(registry_df)
    kept = []
    for _, row in registry_df.iterrows():
        notes = _clean(row.get("notes", "")).lower()
        src = _clean(row.get("polygon_source", "")).lower()
        if "bootstrapped from entity index" in notes and src in ("geopr", "joshua"):
            continue
        kept.append(row)
    out = normalize_registry(pd.DataFrame(kept)) if kept else pd.DataFrame(columns=REGISTRY_COLUMNS)
    return out, before - len(out)


def collect_unmapped_names(
    registry_map: dict[str, str],
    index_lookup: dict | None = None,
    within_path: Path = WITHIN_GROUP_XLSX,
    between_entity_names: set[str] | None = None,
) -> list[str]:
    """Names referenced in JR data that do not resolve to a registry polygon_id."""
    names: set[str] = set()
    if within_path.is_file() or within_path.with_suffix(".csv").is_file():
        df = load_within_group(within_path if within_path.is_file() else within_path.with_suffix(".csv"))
        if "ethnography_group" in df.columns:
            names.update(_clean(v) for v in df["ethnography_group"] if _clean(v))
    if between_entity_names:
        names.update(between_entity_names)

    unmapped: list[str] = []
    for name in sorted(names):
        resolved = resolve_polygon_id(name, registry_map, index_lookup)
        if resolved.upper() == name.upper() and name.upper() not in registry_map:
            unmapped.append(name)
    return unmapped

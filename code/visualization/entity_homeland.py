"""Entity homeland model — source-agnostic polygon identity for JR entities.

Each entity in our joking-relationship data should resolve to:
  - which GIS polygon system it belongs to (murdock / greg / geopr / joshua)
  - the polygon ID within that system
  - its parent ethnic group (for sub-clans like "Azande (Abangombi)")

"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


VALID_POLYGON_SOURCES = frozenset({"murdock", "greg", "geopr", "joshua"})


def _clean_label(val: str) -> str:
    """Treat pandas NaN / literal 'nan' as empty."""
    s = str(val or "").strip()
    return "" if not s or s.lower() == "nan" else s


def index_polygon_trusted(name: str, row: dict | Any) -> bool:
    """True when index polygon_id was manually set for this JR name (not auto-guessed)."""
    raw = _clean_label(name if isinstance(name, str) else str(name or ""))
    pid = _clean_label(str(row.get("polygon_id", "") if hasattr(row, "get") else ""))
    if not raw or not pid:
        return False
    if raw.lower() == pid.lower():
        return True
    if _clean_label(str(row.get("parent_ethnic_group", "") if hasattr(row, "get") else "")):
        return True
    if "(" in raw:
        return True
    return False


@dataclass(frozen=True)
class EntityHomeland:
    """Resolved homeland for one ethnographic entity name."""

    raw_name: str
    canonical_name: str
    entity_type: str
    parent_ethnic_group: str
    polygon_source: str  # murdock | greg | geopr | joshua | unresolved
    polygon_id: str  # NAME in Murdock, G1SHORTNAM in GREG, group in GeoEPR, etc.
    region: str
    lat: float | None = None
    lon: float | None = None

    @property
    def homeland_key(self) -> str:
        """Stable key for grouping entities that share the same homeland polygon."""
        if self.polygon_source in VALID_POLYGON_SOURCES and self.polygon_id:
            return f"{self.polygon_source}:{self.polygon_id.upper()}"
        if self.parent_ethnic_group:
            return f"parent:{self.parent_ethnic_group.strip().upper()}"
        return f"entity:{self.raw_name.strip().upper()}"

    @property
    def display_group(self) -> str:
        """Parent ethnic group name for map labels, or canonical/raw name."""
        return self.parent_ethnic_group or self.canonical_name or self.raw_name

    @property
    def is_resolved(self) -> bool:
        return self.polygon_source in VALID_POLYGON_SOURCES and bool(self.polygon_id or self.lat)


def infer_parent_group(raw_name: str, maps_to: str = "") -> str:
    """Derive parent ethnic group from index field or parenthetical name."""
    parent = (maps_to or "").strip()
    if parent:
        return parent
    outer = re.sub(r"\s*\(.*?\)", "", raw_name).strip()
    if outer and outer != raw_name.strip():
        return outer
    return ""


def _ethnic_group_label(h: EntityHomeland) -> str:
    for candidate in (h.parent_ethnic_group, h.canonical_name, h.raw_name):
        s = _clean_label(candidate)
        if s:
            return s.upper()
    return ""


def same_ethnic_group(a: EntityHomeland, b: EntityHomeland) -> bool:
    """True when two entities belong to the same ethnic group (type-ii, not cross-group)."""
    if a.homeland_key and b.homeland_key and a.homeland_key == b.homeland_key:
        return True
    pa = _ethnic_group_label(a)
    pb = _ethnic_group_label(b)
    if pa and pb and pa == pb:
        return True
    return False


def homeland_from_resolved(resolved, eth_row=None) -> EntityHomeland:
    """Build EntityHomeland from EntityResolver.ResolvedEntity + optional index row."""
    from entity_resolver import ResolvedEntity  # local import avoids cycle at module load

    if not isinstance(resolved, ResolvedEntity):
        raise TypeError("expected ResolvedEntity")

    raw = resolved.raw_name
    maps_to = ""
    entity_type = ""
    if eth_row is not None:
        maps_to = _clean_label(
            eth_row.get("parent_ethnic_group", eth_row.get("maps_to_ethnic_group", ""))
        )
        entity_type = _clean_label(eth_row.get("type", eth_row.get("entity_type", "")))

    parent = infer_parent_group(raw, maps_to)

    polygon_source = resolved.source if resolved.source != "unresolved" else "unresolved"
    polygon_id = ""
    if polygon_source == "murdock":
        polygon_id = (resolved.murdock_name or "").strip()
    elif polygon_source in ("greg", "geopr"):
        polygon_id = (resolved.greg_name or "").strip()
    elif polygon_source == "joshua":
        polygon_id = (resolved.canonical or raw).strip()

    return EntityHomeland(
        raw_name=raw,
        canonical_name=resolved.canonical or raw,
        entity_type=entity_type,
        parent_ethnic_group=parent,
        polygon_source=polygon_source,
        polygon_id=polygon_id,
        region=resolved.region or "",
        lat=resolved.lat,
        lon=resolved.lon,
    )


def homeland_to_entity_meta(
    h: EntityHomeland, color: str, source: str, polygon_group_id: str = "",
) -> dict:
    """Serialize homeland for map JavaScript ENTITY_INFO."""
    meta = {
        "lat": h.lat,
        "lon": h.lon,
        "color": color,
        "source": source if source != "unresolved" else h.polygon_source,
        "region": h.region,
        "parent_group": h.parent_ethnic_group,
        "polygon_source": h.polygon_source,
        "polygon_id": h.polygon_id,
        "homeland_key": h.homeland_key,
        "display_group": h.display_group,
        "polygon_group_id": polygon_group_id or (h.polygon_id or "").upper(),
    }
    # Legacy fields kept for map.js compatibility
    if h.polygon_source == "murdock":
        meta["murdock_name"] = h.polygon_id
    elif h.polygon_source in ("greg", "geopr"):
        meta["greg_name"] = h.polygon_id
    else:
        meta["murdock_name"] = None
        meta["greg_name"] = None
    return meta


# ── JR type labels & intensity scale ─────────────────────────────────────────

KIN_TYPES: set[str] = {"kin_role"}

GROUP_TYPES: set[str] = {
    "group", "clan", "lineage", "caste", "age_set",
    "patronym", "regional group", "ethnic group",
}


def classify_within_entity_types(a_type: str, b_type: str) -> str | None:
    """Return 'type_i', 'type_ii', or None."""
    a_type = (a_type or "").strip().lower()
    b_type = (b_type or "").strip().lower()
    if a_type in KIN_TYPES or b_type in KIN_TYPES:
        return "type_i"
    if a_type in GROUP_TYPES or b_type in GROUP_TYPES:
        return "type_ii"
    if a_type == "person" or b_type == "person":
        return "type_ii"
    return None


def compute_intensity(n_i: int, n_ii: int, n_iii: int) -> int:
    """Intensity scale 0–5 from type counts."""
    n_types = sum([n_i > 0, n_ii > 0, n_iii > 0])
    if n_types == 0:
        return 0
    if n_types >= 3:
        return 5
    if n_types == 2:
        return 4
    if n_iii > 0:
        return 3
    if n_ii > 0:
        return 2
    return 1


def same_ethnic_from_annotations(ann_a: dict, ann_b: dict) -> bool:
    """True when two annotated endpoints belong to the same ethnic group."""
    ka = (ann_a.get("homeland_key") or "").strip()
    kb = (ann_b.get("homeland_key") or "").strip()
    if ka and kb and ka == kb:
        return True
    pa = _clean_label(ann_a.get("parent_group", "")).upper()
    pb = _clean_label(ann_b.get("parent_group", "")).upper()
    if pa and pb and pa == pb:
        return True
    return False

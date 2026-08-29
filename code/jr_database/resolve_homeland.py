"""Resolve entity names to Murdock / GREG / GeoEPR homelands."""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import geopandas as gpd
import pandas as pd

_CODE = Path(__file__).resolve().parent.parent
if str(_CODE) not in sys.path:
    sys.path.insert(0, str(_CODE))
_VIS = _CODE / "visualization"
if str(_VIS) not in sys.path:
    sys.path.insert(0, str(_VIS))

from entity_index import build_lookup, load_index, lookup_row, _icmid_index_sheet_exists  # noqa: E402
from polygon_registry import (  # noqa: E402
    build_manual_alias_map,
    load_registry,
    lookup_name_variants,
)

from jr_database.config import (  # noqa: E402
    ETHNIC_ENTITY_INDEX_XLSX,
    GEOEPR_SHP,
    GREG_SHP,
    MURDOCK_SHP,
    POLYGON_GROUP_REGISTRY_XLSX,
)

VALID_HOMELAND = frozenset({"murdock", "greg", "geopr"})


def _clean(val: Any) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _norm_key(name: str) -> str:
    s = _clean(name)
    s = re.sub(r"^the\s+", "", s, flags=re.I)
    s = re.sub(r"[^\w\s\-']", " ", s, flags=re.UNICODE)
    s = re.sub(r"\s+", " ", s).strip().casefold()
    return s


@dataclass(frozen=True)
class HomelandHit:
    polygon_source: str  # murdock | greg | geopr | ""
    polygon_id: str
    display_name: str
    match_method: str  # index | registry | gis_exact | ""
    resolve_source: str = ""  # provenance for the mapping (wiki URL, gis, …)


class HomelandResolver:
    def __init__(self) -> None:
        if ETHNIC_ENTITY_INDEX_XLSX.is_file() or _icmid_index_sheet_exists():
            self._index_lookup = build_lookup(load_index())
        else:
            self._index_lookup = {}
        registry = load_registry() if POLYGON_GROUP_REGISTRY_XLSX.is_file() else pd.DataFrame()
        self._alias_map = build_manual_alias_map(registry) if not registry.empty else {}
        self._registry_by_id = {
            _clean(r["polygon_id"]).upper(): r
            for _, r in registry.iterrows()
            if _clean(r.get("polygon_id"))
        } if not registry.empty else {}
        self._gis = self._build_gis_maps()

    def _build_gis_maps(self) -> dict[str, dict[str, tuple[str, str]]]:
        """source -> norm_name -> (polygon_id, display_name)."""
        out: dict[str, dict[str, tuple[str, str]]] = {
            "murdock": {},
            "greg": {},
            "geopr": {},
        }
        if MURDOCK_SHP.is_file():
            g = gpd.read_file(MURDOCK_SHP)
            for _, r in g.iterrows():
                name = _clean(r.get("NAME"))
                if not name:
                    continue
                key = _norm_key(name)
                out["murdock"][key] = (name.upper(), name)
        if GREG_SHP.is_file():
            g = gpd.read_file(GREG_SHP)
            for col_id, col_name in (
                ("G1SHORTNAM", "G1SHORTNAM"),
                ("G1LONGNAM", "G1LONGNAM"),
                ("G2SHORTNAM", "G2SHORTNAM"),
                ("G3SHORTNAM", "G3SHORTNAM"),
            ):
                if col_name not in g.columns:
                    continue
                for _, r in g.iterrows():
                    name = _clean(r.get(col_name))
                    if not name or name.lower() == "nan":
                        continue
                    key = _norm_key(name)
                    out["greg"].setdefault(key, (name.upper(), name))
        if GEOEPR_SHP.is_file():
            g = gpd.read_file(GEOEPR_SHP)
            for _, r in g.iterrows():
                name = _clean(r.get("group"))
                if not name:
                    continue
                gid = _clean(r.get("gwgroupid")) or name.upper()
                key = _norm_key(name)
                out["geopr"].setdefault(key, (str(gid), name))
        return out

    def resolve(self, name: str) -> HomelandHit:
        raw = _clean(name)
        if not raw:
            return HomelandHit("", "", "", "", "")

        # 1) entity index (manual — preferred; carries resolve_source)
        row = lookup_row(self._index_lookup, raw)
        if row is not None:
            src = _clean(row.get("polygon_source")).lower().replace("geoepr", "geopr")
            pid = _clean(row.get("polygon_id")).upper()
            if src in VALID_HOMELAND and pid:
                disp = _clean(row.get("canonical_name")) or _clean(row.get("parent_ethnic_group")) or raw
                rsrc = _clean(row.get("resolve_source")) or "ethnic_entity_index"
                return HomelandHit(src, pid, disp, "index", rsrc)

        # 2) registry aliases → polygon_id
        for variant in lookup_name_variants(raw):
            pid = self._alias_map.get(variant)
            if not pid:
                continue
            pid = _clean(pid).upper()
            reg = self._registry_by_id.get(pid)
            if reg is None:
                continue
            src = _clean(reg.get("polygon_source")).lower().replace("geoepr", "geopr")
            disp = _clean(reg.get("display_name")) or pid.title()
            if src in VALID_HOMELAND and pid:
                rsrc = _clean(reg.get("notes")) or "polygon_group_registry"
                return HomelandHit(src, pid, disp, "registry", rsrc)

        # 3) GIS exact / casefold
        key = _norm_key(raw)
        for source in ("murdock", "greg", "geopr"):
            hit = self._gis[source].get(key)
            if hit:
                pid, disp = hit
                return HomelandHit(source, pid, disp, "gis_exact", f"gis:{source}")

        return HomelandHit("", "", raw, "", "")


@lru_cache(maxsize=1)
def get_resolver() -> HomelandResolver:
    return HomelandResolver()

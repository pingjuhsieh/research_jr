"""Resolve ethnographic entity names to Murdock / GREG / GeoEPR homelands.

Matching policy: **manual only** — no GIS guessing, no display_name matching.
  1. registry aliases column (e.g. Fulani → FULBE)
  2. entity_index row with polygon_source + polygon_id you entered by hand
Unmatched → unmatched_homelands.xlsx
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely.ops import unary_union

from config import (
    ETHNIC_ENTITY_INDEX_XLSX,
    GEOEPR_SHP,
    GREG_SHP,
    JOSHUA_CSV,
    MURDOCK_SHP,
    POLYGON_GROUP_REGISTRY_XLSX,
    REGION_COLORS,
    DEFAULT_REGION_COLOR,
)
from entity_homeland import VALID_POLYGON_SOURCES, EntityHomeland, homeland_from_resolved
from entity_index import build_lookup, load_index
from polygon_registry import (
    build_manual_alias_map,
    build_registry_by_id,
    gis_labels_for_registry_row,
    load_registry,
    lookup_name_variants,
)

JP_BAD_COUNTRIES = {
    "Papua New Guinea", "India", "Mexico", "Brazil",
    "Indonesia", "Philippines", "Russia", "Peru",
}

_SOURCE_MAP = {
    "murdock": "murdock",
    "greg": "greg",
    "geopr": "geopr",
    "geoepr": "geopr",
    "epr": "geopr",
    "joshuaproject": "joshua",
    "joshua project": "joshua",
    "joshua_project": "joshua",
    "joshua": "joshua",
    "jp": "joshua",
}


def _clean(val: Any) -> str:
    s = str(val).strip() if val is not None else ""
    return "" if s.lower() == "nan" else s


@dataclass
class ResolvedEntity:
    raw_name: str
    canonical: str
    region: str
    color: str
    source: str  # murdock | greg | geopr | joshua | unresolved
    murdock_name: str | None = None
    greg_name: str | None = None
    lat: float | None = None
    lon: float | None = None


class EntityResolver:
    """Map entity strings to homelands via manual registry aliases + entity index only."""

    def __init__(self) -> None:
        if not ETHNIC_ENTITY_INDEX_XLSX.is_file():
            raise FileNotFoundError(
                f"Entity index not found: {ETHNIC_ENTITY_INDEX_XLSX}\n"
                "Run: uv run python code/visualization/prepare.py data --import-keerthana"
            )
        index_path = ETHNIC_ENTITY_INDEX_XLSX

        self.ethnics = pd.read_excel(index_path)
        if "entity_type" in self.ethnics.columns and "type" not in self.ethnics.columns:
            self.ethnics = self.ethnics.rename(columns={"entity_type": "type"})
        if "polygon_id" in self.ethnics.columns and "MurdockShapefile" not in self.ethnics.columns:
            self.ethnics = self.ethnics.rename(columns={"polygon_id": "MurdockShapefile"})
        if "polygon_source" in self.ethnics.columns and "Source" not in self.ethnics.columns:
            self.ethnics = self.ethnics.rename(columns={"polygon_source": "Source"})
        if "parent_ethnic_group" in self.ethnics.columns and "maps_to_ethnic_group" not in self.ethnics.columns:
            self.ethnics = self.ethnics.rename(columns={"parent_ethnic_group": "maps_to_ethnic_group"})
        self.shp = gpd.read_file(MURDOCK_SHP)
        self.greg = gpd.read_file(GREG_SHP).to_crs("EPSG:4326")
        self.epr = gpd.read_file(GEOEPR_SHP).to_crs("EPSG:4326")
        self.jp = pd.read_csv(JOSHUA_CSV)

        self.shp_lu = {str(r["NAME"]).upper(): r for _, r in self.shp.iterrows()}
        self.eth_by_canonical = self._build_eth_index(self.ethnics, "canonical_name")
        self.eth_by_raw = self._build_eth_index(self.ethnics, "raw_value")

        self.index_lookup = build_lookup(load_index())
        self.registry_df = load_registry() if POLYGON_GROUP_REGISTRY_XLSX.is_file() else None
        self.manual_alias_map = (
            build_manual_alias_map(self.registry_df) if self.registry_df is not None else {}
        )
        self.registry_by_id = build_registry_by_id(self.registry_df) if self.registry_df is not None else {}

    @staticmethod
    def _build_eth_index(ethnics: pd.DataFrame, col: str) -> dict[str, pd.Series]:
        idx: dict[str, pd.Series] = {}
        for _, row in ethnics.iterrows():
            key = _clean(row.get(col, "")).lower()
            if key and key not in idx:
                idx[key] = row
        return idx

    def _find_eth_row(self, name: str) -> pd.Series | None:
        key = name.strip().lower()
        eth = self.eth_by_canonical.get(key)
        if eth is None:
            eth = self.eth_by_raw.get(key)
        if eth is not None:
            return eth
        m_paren = re.search(r"\((.+?)\)", name)
        inner = m_paren.group(1).strip() if m_paren else None
        outer = re.sub(r"\s*\(.*?\)", "", name).strip()
        for candidate in (inner, outer):
            if not candidate:
                continue
            eth = self.eth_by_canonical.get(candidate.lower())
            if eth is None:
                eth = self.eth_by_raw.get(candidate.lower())
            if eth is not None:
                return eth
        return None

    def _murdock_lookup(self, name_value: str) -> tuple[float, float, str] | None:
        if not name_value:
            return None
        for part in [p.strip() for p in str(name_value).split(",") if p.strip()]:
            key = part.upper()
            if key in self.shp_lu:
                r = self.shp_lu[key]
                return float(r["LAT"]), float(r["LON"]), key
        return None

    def _greg_lookup(self, name_value: str) -> tuple[float, float, str] | None:
        if not name_value:
            return None
        for part in [p.strip() for p in str(name_value).split(",") if p.strip()]:
            sub = self.greg[self.greg["G1SHORTNAM"].str.lower() == part.lower()]
            if not sub.empty:
                geom = unary_union(sub.geometry)
                if geom is None or geom.is_empty:
                    continue
                c = geom.centroid
                if c.is_empty:
                    continue
                return c.y, c.x, str(sub.iloc[0]["G1SHORTNAM"])
        return None

    def _epr_lookup(self, name_value: str) -> tuple[float, float, str] | None:
        if not name_value:
            return None
        for part in [p.strip() for p in str(name_value).split(",") if p.strip()]:
            sub = self.epr[self.epr["group"].str.lower() == part.lower()]
            if not sub.empty:
                geom = unary_union(sub.geometry)
                if geom is None or geom.is_empty:
                    continue
                c = geom.centroid
                if c.is_empty:
                    continue
                return c.y, c.x, str(sub.iloc[0]["group"])
        return None

    def _jp_lookup(self, name_value: str, country_hint: str = "") -> tuple[float, float] | None:
        if not name_value:
            return None
        for part in [p.strip() for p in str(name_value).split(",") if p.strip()]:
            part_l = part.lower()
            hits = self.jp[self.jp["people_group"].str.lower() == part_l]
            hits = hits[~hits["country"].isin(JP_BAD_COUNTRIES)]
            if country_hint:
                first = country_hint.split(",")[0].strip().lower()
                ch = hits[hits["country"].str.lower() == first]
                if not ch.empty:
                    hits = ch
            if not hits.empty:
                r = hits.iloc[0]
                return float(r["latitude"]), float(r["longitude"])
        return None

    def _lookup_in_source(
        self,
        source: str,
        polygon_id: str,
        country: str = "",
    ) -> ResolvedEntity | None:
        if source == "murdock":
            hit = self._murdock_lookup(polygon_id)
            if hit:
                lat, lon, mkey = hit
                return ResolvedEntity(
                    raw_name="", canonical="", region="", color="",
                    source="murdock", murdock_name=mkey, lat=lat, lon=lon,
                )
        elif source == "greg":
            hit = self._greg_lookup(polygon_id)
            if hit:
                lat, lon, gname = hit
                return ResolvedEntity(
                    raw_name="", canonical="", region="", color="",
                    source="greg", greg_name=gname, lat=lat, lon=lon,
                )
        elif source == "geopr":
            hit = self._epr_lookup(polygon_id)
            if hit:
                lat, lon, gname = hit
                return ResolvedEntity(
                    raw_name="", canonical="", region="", color="",
                    source="geopr", greg_name=gname, lat=lat, lon=lon,
                )
        elif source == "joshua":
            hit = self._jp_lookup(polygon_id, country)
            if hit:
                lat, lon = hit
                return ResolvedEntity(
                    raw_name="", canonical="", region="", color="",
                    source="joshua", lat=lat, lon=lon,
                )
        return None

    def _resolve_via_registry_alias(
        self,
        name: str,
        country: str = "",
    ) -> tuple[ResolvedEntity, str] | None:
        """Only when name is in registry aliases (or is polygon_id) — manual entries."""
        if not self.manual_alias_map:
            return None
        canonical = None
        for key in lookup_name_variants(name):
            canonical = self.manual_alias_map.get(key)
            if canonical:
                break
        if not canonical:
            return None
        reg_row = self.registry_by_id.get(canonical)
        if reg_row is None:
            return None
        src = _clean(reg_row.get("polygon_source", "")).lower()
        if src not in VALID_POLYGON_SOURCES:
            return None
        for label in gis_labels_for_registry_row(reg_row):
            hit = self._lookup_in_source(src, label, country)
            if hit is not None:
                return hit, canonical
        return None

    def resolve(self, entity_name: str) -> ResolvedEntity | None:
        raw = entity_name.strip()
        eth = self._find_eth_row(raw)
        country = _clean(eth.get("country", "")) if eth is not None else ""
        region = _clean(eth.get("region", "")) if eth is not None else ""
        canonical = (_clean(eth.get("canonical_name", "")) if eth is not None else "") or raw
        color = REGION_COLORS.get(region, DEFAULT_REGION_COLOR)

        reg_result = self._resolve_via_registry_alias(raw, country)
        if reg_result is not None:
            hit, _canonical_pid = reg_result
            return ResolvedEntity(
                raw_name=raw,
                canonical=canonical,
                region=region,
                color=color,
                source=hit.source,
                murdock_name=hit.murdock_name,
                greg_name=hit.greg_name,
                lat=hit.lat,
                lon=hit.lon,
            )

        if eth is None:
            return ResolvedEntity(
                raw_name=raw, canonical=raw, region="", color=DEFAULT_REGION_COLOR,
                source="unresolved",
            )

        source_raw = _clean(
            eth.get("polygon_source") or eth.get("Source") or eth.get("homeland_source", "")
        ).lower()
        polygon_id = _clean(
            eth.get("polygon_id") or eth.get("MurdockShapefile") or eth.get("murdock_shapefile", "")
        )

        preferred = _SOURCE_MAP.get(source_raw, "")
        if preferred not in VALID_POLYGON_SOURCES or not polygon_id:
            return ResolvedEntity(
                raw_name=raw, canonical=canonical, region=region, color=color,
                source="unresolved",
            )

        hit = self._lookup_in_source(preferred, polygon_id, country)
        if hit is None:
            return ResolvedEntity(
                raw_name=raw, canonical=canonical, region=region, color=color,
                source="unresolved",
            )

        return ResolvedEntity(
            raw_name=raw,
            canonical=canonical,
            region=region,
            color=color,
            source=hit.source,
            murdock_name=hit.murdock_name,
            greg_name=hit.greg_name,
            lat=hit.lat,
            lon=hit.lon,
        )

    def resolve_homeland(self, entity_name: str) -> EntityHomeland | None:
        resolved = self.resolve(entity_name)
        if resolved is None:
            return None
        eth = self._find_eth_row(entity_name.strip())
        return homeland_from_resolved(resolved, eth)

    def verify_index_row(self, row: pd.Series | dict) -> tuple[bool, str]:
        raw = _clean(row.get("raw_value", ""))
        country = _clean(row.get("country", ""))
        if raw and self._resolve_via_registry_alias(raw, country) is not None:
            return True, "ok_via_registry_alias"

        source_raw = _clean(row.get("polygon_source") or row.get("Source", "")).lower()
        polygon_id = _clean(
            row.get("polygon_id") or row.get("MurdockShapefile") or row.get("murdock_shapefile", "")
        )
        preferred = _SOURCE_MAP.get(source_raw, "")
        if preferred not in VALID_POLYGON_SOURCES:
            return False, "missing_or_invalid_polygon_source"
        if not polygon_id:
            return False, "missing_polygon_id"
        if self._lookup_in_source(preferred, polygon_id, country) is None:
            return False, f"polygon_not_found_in_{preferred}"
        return True, "ok"

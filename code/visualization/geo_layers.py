"""Load and simplify GIS layers for Leaflet embedding."""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from config import AFRICA_BBOX, GEOEPR_SHP, GREG_SHP, MURDOCK_SHP, THP_CSV


def _geom_to_json(geom) -> dict:
    return json.loads(gpd.GeoSeries([geom]).to_json())["features"][0]["geometry"]


def _clip_africa(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    minx, miny, maxx, maxy = AFRICA_BBOX
    return gdf.cx[minx:maxx, miny:maxy].copy().to_crs("EPSG:4326")


def load_thp_lookup() -> dict[str, float | None]:
    try:
        df = pd.read_csv(THP_CSV)
        out: dict[str, float | None] = {}
        for _, row in df.iterrows():
            key = str(row["murdock_name"]).strip().upper()
            val = row.get("THP_Broad")
            out[key] = None if pd.isna(val) else float(val)
        return out
    except FileNotFoundError:
        return {}


def murdock_geojson(simplify: float = 0.03) -> str:
    thp_lu = load_thp_lookup()
    shp = gpd.read_file(MURDOCK_SHP)
    shp["geometry"] = shp.geometry.simplify(simplify, preserve_topology=True)
    feats = []
    for _, r in shp.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        name = str(r["NAME"])
        feats.append({
            "type": "Feature",
            "properties": {
                "NAME": name,
                "LAT": float(r["LAT"]),
                "LON": float(r["LON"]),
                "THP": thp_lu.get(name.strip().upper()),
            },
            "geometry": _geom_to_json(g),
        })
    return json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))


def greg_geojson(simplify: float = 0.05) -> str:
    greg = _clip_africa(gpd.read_file(GREG_SHP))
    greg["geometry"] = greg.geometry.simplify(simplify, preserve_topology=True)
    greg = greg[greg.geometry.notna() & ~greg.geometry.is_empty]
    feats = []
    for _, r in greg.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        name = str(r["G1SHORTNAM"] or "Unknown")
        feats.append({
            "type": "Feature",
            "properties": {
                "NAME": name,
                "LONG_NAME": str(r["G1LONGNAM"] or name),
                "COUNTRY": str(r.get("FIPS_CNTRY") or ""),
            },
            "geometry": _geom_to_json(g),
        })
    return json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))


def geoepr_geojson(simplify: float = 0.05) -> str:
    epr = _clip_africa(gpd.read_file(GEOEPR_SHP))
    epr["geometry"] = epr.geometry.simplify(simplify, preserve_topology=True)
    epr = epr[epr.geometry.notna() & ~epr.geometry.is_empty]
    feats = []
    for _, r in epr.iterrows():
        g = r.geometry
        if g is None or g.is_empty:
            continue
        name = str(r["group"] or "Unknown")
        feats.append({
            "type": "Feature",
            "properties": {
                "NAME": name,
                "STATE": str(r.get("statename") or ""),
                "FROM": int(r["from"]) if pd.notna(r.get("from")) else 0,
                "TO": int(r["to"]) if pd.notna(r.get("to")) else 0,
                "TYPE": str(r.get("type") or ""),
            },
            "geometry": _geom_to_json(g),
        })
    return json.dumps({"type": "FeatureCollection", "features": feats}, separators=(",", ":"))

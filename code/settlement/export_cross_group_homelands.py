#!/usr/bin/env python3
"""Export homeland units for groups with cross-group joking relationships.

Uses the Visualization pipeline when lookup tables exist; otherwise falls back to
``output/visualization/group_intensity_summary.csv`` (groups with n_iii > 0) plus
``data/lookup/jr_polygon_aliases.csv`` for name collisions.

Output: output/settlement/cross_group_homeland_units.csv

Usage (from project root):
    uv run python -B code/settlement/export_cross_group_homelands.py
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import pandas as pd

SETTLEMENT_DIR = Path(__file__).resolve().parent
PIPELINE_ROOT = SETTLEMENT_DIR.parent.parent
VIS_DIR = PIPELINE_ROOT / "code" / "visualization"
OUT_DIR = PIPELINE_ROOT / "output" / "settlement"
OUT_CSV = OUT_DIR / "cross_group_homeland_units.csv"
ALIASES_CSV = PIPELINE_ROOT / "data" / "lookup" / "jr_polygon_aliases.csv"
INTENSITY_CSV = PIPELINE_ROOT / "output" / "visualization" / "group_intensity_summary.csv"

SOURCE_PRIORITY = {"murdock": 0, "greg": 1, "geopr": 2, "point": 3}


def _load_aliases() -> dict[str, tuple[str, str]]:
    """group_id -> (polygon_source, polygon_name)."""
    out: dict[str, tuple[str, str]] = {}
    if not ALIASES_CSV.is_file():
        return out
    df = pd.read_csv(ALIASES_CSV)
    for _, row in df.iterrows():
        gid = str(row.get("group_id", "")).strip().upper()
        src = str(row.get("polygon_source", "")).strip().lower()
        name = str(row.get("polygon_name", "")).strip()
        if gid and src and name:
            out[gid] = (src, name)
    return out


def _export_from_visualization() -> pd.DataFrame | None:
    """Use entity resolver + between-group data (same logic as the JR map)."""
    if str(VIS_DIR) not in sys.path:
        sys.path.insert(0, str(VIS_DIR))

    from config import BETWEEN_GROUP_JOKING_XLSX, POLYGON_GROUP_REGISTRY_XLSX
    from build_cross_group_map import _build_highlight_data, _load_between_groups
    from entity_index import build_lookup, load_index
    from entity_resolver import EntityResolver
    from polygon_registry import build_name_to_polygon_map, load_registry

    input_path = BETWEEN_GROUP_JOKING_XLSX
    if not input_path.is_file():
        alt = (
            PIPELINE_ROOT
            / "output"
            / "llm_ehraf"
            / "export"
            / "llm_ehraf_cross_group.csv"
        )
        if alt.is_file():
            input_path = alt
        else:
            return None

    registry_df = load_registry() if POLYGON_GROUP_REGISTRY_XLSX.is_file() else pd.DataFrame()
    registry_map = build_name_to_polygon_map(registry_df) if not registry_df.empty else {}
    from config import ETHNIC_ENTITY_INDEX_XLSX

    index_lookup = build_lookup(load_index()) if ETHNIC_ENTITY_INDEX_XLSX.is_file() else {}
    resolver = EntityResolver()
    df = _load_between_groups(input_path)
    murdock_h, greg_h, geopr_h, markers, entity_meta, partner_map, *_ = _build_highlight_data(
        df, resolver, registry_map, index_lookup,
    )

    rows: list[dict] = []
    seen: set[tuple[str, str]] = set()

    def _add(source: str, name: str, group_id: str = "") -> None:
        key = (source, name.strip().upper())
        if not name or key in seen:
            return
        seen.add(key)
        rows.append({
            "group_id": group_id or name.strip().upper(),
            "polygon_source": source,
            "polygon_name": name.strip(),
            "lat": "",
            "lon": "",
        })

    for name in murdock_h:
        _add("murdock", name)
    for name in greg_h:
        _add("greg", name)
    for name in geopr_h:
        _add("geopr", name)
    for m in markers:
        rows.append({
            "group_id": m["label"].strip().upper(),
            "polygon_source": "point",
            "polygon_name": "",
            "lat": m["lat"],
            "lon": m["lon"],
        })

    # Groups in partner_map but only as cross-group endpoints
    cross_entities = {e for e, partners in partner_map.items() if partners}
    for entity in sorted(cross_entities):
        meta = entity_meta.get(entity, {})
        src = (meta.get("polygon_source") or meta.get("source") or "").lower()
        if src == "murdock" and meta.get("murdock_name"):
            _add("murdock", meta["murdock_name"], meta.get("polygon_group_id", ""))
        elif src in ("greg", "geopr") and meta.get("greg_name"):
            _add(src, meta["greg_name"], meta.get("polygon_group_id", ""))
        elif meta.get("lat") is not None and meta.get("lon") is not None:
            gid = (meta.get("polygon_group_id") or entity).strip().upper()
            rows.append({
                "group_id": gid,
                "polygon_source": "point",
                "polygon_name": "",
                "lat": meta["lat"],
                "lon": meta["lon"],
            })

    if not rows:
        return None
    return pd.DataFrame(rows).drop_duplicates()


def _export_from_intensity_summary() -> pd.DataFrame:
    """Fallback: groups with n_iii > 0 from visualization intensity summary."""
    if not INTENSITY_CSV.is_file():
        raise FileNotFoundError(
            f"Missing {INTENSITY_CSV}. Run: bash code/visualization/scripts/run_map.sh"
        )

    import geopandas as gpd

    gi = pd.read_csv(INTENSITY_CSV)
    cross = gi[gi["n_iii"] > 0].copy()
    cross["group_id"] = cross["group"].astype(str).str.strip().str.upper()

    murdock = gpd.read_file(PIPELINE_ROOT / "data" / "gis" / "murdock" / "Murdock_Map_2020.shp")
    greg = gpd.read_file(PIPELINE_ROOT / "data" / "gis" / "greg" / "GREG.shp")
    geoepr = gpd.read_file(PIPELINE_ROOT / "data" / "gis" / "geoepr" / "GeoEPR-2021.shp")

    murdock_names = {str(n).strip().upper() for n in murdock["NAME"]}
    greg_names = {str(n).strip().upper() for n in greg["G1SHORTNAM"]}
    geoepr_names = {str(n).strip().upper() for n in geoepr["group"]}

    aliases = _load_aliases()
    rows: list[dict] = []

    for gid in cross["group_id"]:
        if gid in aliases:
            src, pname = aliases[gid]
            rows.append({
                "group_id": gid,
                "polygon_source": src,
                "polygon_name": pname,
                "lat": "",
                "lon": "",
            })
            continue

        if gid in murdock_names:
            rows.append({"group_id": gid, "polygon_source": "murdock", "polygon_name": gid.title(), "lat": "", "lon": ""})
        elif gid in greg_names:
            rows.append({"group_id": gid, "polygon_source": "greg", "polygon_name": gid.title(), "lat": "", "lon": ""})
        elif gid in geoepr_names:
            rows.append({"group_id": gid, "polygon_source": "geopr", "polygon_name": gid.title(), "lat": "", "lon": ""})
        else:
            print(f"  WARNING: no GIS match for cross-group group {gid}")

    return pd.DataFrame(rows).drop_duplicates()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    df: pd.DataFrame | None = None
    try:
        df = _export_from_visualization()
        if df is not None:
            print(f"Exported {len(df)} homeland units from visualization pipeline")
    except Exception as exc:
        print(f"visualization export unavailable ({exc}); using intensity-summary fallback")

    if df is None or df.empty:
        df = _export_from_intensity_summary()
        print(f"Exported {len(df)} homeland units from group_intensity_summary.csv")

    df = df.sort_values(["polygon_source", "group_id"]).reset_index(drop=True)
    df.to_csv(OUT_CSV, index=False, quoting=csv.QUOTE_MINIMAL)
    print(f"Wrote → {OUT_CSV}")


if __name__ == "__main__":
    main()

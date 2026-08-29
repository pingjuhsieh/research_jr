#!/usr/bin/env python3
"""
Build an interactive Leaflet map of joking relationships
(cross-group, within-group, and kinship) on ethnic homelands.

Data sources under output/jr_database/:
  cross_group_map.xlsx, within_group.xlsx, jr_records.json
  (from sync_from_jr_database / run.sh)

Usage (from project root):
    bash code/jr_database/scripts/run.sh
    # or map-only:
    bash code/visualization/scripts/run_map.sh
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

_VIS_DIR = Path(__file__).resolve().parent
if str(_VIS_DIR) not in sys.path:
    sys.path.insert(0, str(_VIS_DIR))

import pandas as pd

from config import (
    CROSS_GROUP_MAP_HTML,
    CROSS_GROUP_MAP_XLSX,
    INTENSITY_COLORS,
    JR_RECORDS_JSON,
    LOOKUP_ROOT,
    OUTPUT_DIR,
    POLYGON_GROUP_REGISTRY_XLSX,
    REGION_ALIAS,
    REGION_COLORS,
    UNMAPPED_REGISTRY_CSV,
    UNRESOLVED_CSV,
    WITHIN_GROUP_XLSX,
)
from jr_tables import load_within_group
from entity_homeland import (
    EntityHomeland,
    KIN_TYPES,
    VALID_POLYGON_SOURCES,
    homeland_to_entity_meta,
    same_ethnic_from_annotations,
    same_ethnic_group,
)
from entity_index import build_lookup, load_index, lookup_row
from entity_resolver import EntityResolver, ResolvedEntity
from geo_layers import geoepr_geojson, greg_geojson, murdock_geojson
from polygon_registry import (
    SOURCE_PRIORITY,
    bootstrap_from_entity_index,
    build_name_to_polygon_map,
    collect_unmapped_names,
    load_registry,
    normalize_entity_for_pair,
    resolve_polygon_id,
    save_registry,
)

_TEMPLATES = Path(__file__).resolve().parent / "templates"


def _clean_str(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _norm_record_id(val) -> str:
    """Normalize pandas float IDs (759.0) to match JR_RECORDS keys (759)."""
    s = _clean_str(val)
    if not s:
        return ""
    try:
        f = float(s)
        if f == int(f):
            return str(int(f))
    except ValueError:
        pass
    return s


def _render_map_html(
    *,
    stats_line: str,
    intensity_legend: str,
    murdock_gj: str,
    greg_gj: str,
    geoepr_gj: str,
    entity_meta: dict,
    partner_map: dict,
    cross_pair_types: dict,
    region_colors: dict,
    intensity_colors: dict,
    within_group_map: dict,
    group_intensity: dict,
    jr_records: dict,
    cross_pair_records: dict,
    within_pair_records: dict,
) -> str:
    """Assemble self-contained HTML from templates/ + injected JSON."""
    html = (_TEMPLATES / "map.html").read_text(encoding="utf-8")
    css = (_TEMPLATES / "map.css").read_text(encoding="utf-8")
    js = (_TEMPLATES / "map.js").read_text(encoding="utf-8")
    js += "\n" + (_TEMPLATES / "map_jr_detail.js").read_text(encoding="utf-8")
    js = (
        js.replace("__MURDOCK_GJ__", murdock_gj)
        .replace("__GREG_GJ__", greg_gj)
        .replace("__GEOPR_GJ__", geoepr_gj)
        .replace("__ENTITY_INFO__", json.dumps(entity_meta, ensure_ascii=False, separators=(",", ":")))
        .replace("__PARTNER_MAP__", json.dumps(partner_map, ensure_ascii=False, separators=(",", ":")))
        .replace("__CROSS_PAIR_TYPES__", json.dumps(cross_pair_types, ensure_ascii=False, separators=(",", ":")))
        .replace("__REGION_COLORS__", json.dumps(region_colors, separators=(",", ":")))
        .replace(
            "__INTENSITY_COLORS__",
            json.dumps({str(k): v for k, v in intensity_colors.items()}, separators=(",", ":")),
        )
        .replace("__WITHIN_GROUP_MAP__", json.dumps(within_group_map, ensure_ascii=False, separators=(",", ":")))
        .replace("__GROUP_INTENSITY__", json.dumps(group_intensity, ensure_ascii=False, separators=(",", ":")))
        .replace("__JR_RECORDS__", json.dumps(jr_records, ensure_ascii=False, separators=(",", ":")))
        .replace("__CROSS_PAIR_RECORDS__", json.dumps(cross_pair_records, ensure_ascii=False, separators=(",", ":")))
        .replace("__WITHIN_PAIR_RECORDS__", json.dumps(within_pair_records, ensure_ascii=False, separators=(",", ":")))
    )
    return (
        html.replace("__MAP_CSS__", css.strip())
        .replace("__STATS_LINE__", stats_line)
        .replace("__INTENSITY_LEGEND__", intensity_legend)
        .replace("__MAP_JS__", js.strip())
    )


def _polygon_key_from_homeland(h: EntityHomeland, registry_map: dict[str, str]) -> str:
    """Canonical polygon_id for JR grouping."""
    if h.polygon_id:
        return h.polygon_id.upper()
    for candidate in (h.parent_ethnic_group, h.display_group, h.raw_name):
        if candidate:
            return resolve_polygon_id(candidate, registry_map)
    return ""


def _visual_map_key(entity_name: str, meta: dict) -> str:
    """Key for grouping polygons/points on the map."""
    pg = (meta.get("polygon_group_id") or "").strip().upper()
    if pg:
        return pg
    src = meta.get("source", "")
    mn = (meta.get("murdock_name") or "").strip().upper()
    gn = (meta.get("greg_name") or "").strip().upper()
    if src == "murdock" and mn:
        return mn
    if src in ("greg", "geopr") and gn:
        return gn
    return entity_name.strip().upper()


def _build_within_group_map(
    registry_map: dict[str, str],
    index_lookup: dict,
) -> tuple[dict[str, dict], dict[str, list[str]]]:
    """Build within-group JR pairs keyed by polygon_id, with record ID linkage."""
    if not WITHIN_GROUP_XLSX.is_file() and not WITHIN_GROUP_XLSX.with_suffix(".csv").is_file():
        print(f"  WARNING: {WITHIN_GROUP_XLSX} not found — within-group data will be empty")
        return {}, {}

    df = load_within_group()

    within_map: dict[str, dict] = {}
    within_pair_records: dict[str, list[str]] = {}
    seen: dict[str, set] = {}

    for _, row in df.iterrows():
        ethno = str(row.get("ethnography_group", "") or "").strip()
        a = str(row.get("entity_a", "") or row.get("entity_a_canonical", "") or "").strip()
        b = str(row.get("entity_b", "") or row.get("entity_b_canonical", "") or "").strip()
        rid = _norm_record_id(row.get("relationship_id") or row.get("relationship_row_id"))
        a_type = str(row.get("entity_a_type", "") or "").strip().lower()
        b_type = str(row.get("entity_b_type", "") or "").strip().lower()
        if not ethno or not a or not b:
            continue

        jr_type = "type_i" if (a_type in KIN_TYPES or b_type in KIN_TYPES) else "type_ii"
        mkey = resolve_polygon_id(ethno, registry_map, index_lookup)

        if mkey not in within_map:
            within_map[mkey] = {"type_i": [], "type_ii": []}
            seen[mkey] = set()

        pair_key = "|||".join(sorted([a, b]))
        lookup_key = f"{mkey}|||{pair_key}"

        if pair_key in seen[mkey]:
            for bucket in within_map[mkey].values():
                for item in bucket:
                    if "|||".join(sorted([item["a"], item["b"]])) == pair_key:
                        if rid and rid not in item.get("record_ids", []):
                            item.setdefault("record_ids", []).append(rid)
            if rid:
                within_pair_records.setdefault(lookup_key, [])
                if rid not in within_pair_records[lookup_key]:
                    within_pair_records[lookup_key].append(rid)
            continue

        seen[mkey].add(pair_key)
        entry = {"a": a, "b": b, "record_ids": [rid] if rid else []}
        within_map[mkey][jr_type].append(entry)
        if rid:
            within_pair_records[lookup_key] = [rid]

    n_pairs = sum(len(v["type_i"]) + len(v["type_ii"]) for v in within_map.values())
    print(f"  Within-group map: {len(within_map)} polygon groups, {n_pairs} unique pairs")
    return within_map, within_pair_records


def _build_cross_pair_records(df: pd.DataFrame) -> dict[str, list[str]]:
    out: dict[str, list[str]] = defaultdict(list)
    for _, row in df.iterrows():
        a = _clean_str(row.get("entity_a"))
        b = _clean_str(row.get("entity_b"))
        rid = _norm_record_id(row.get("relationship_row_id"))
        if not a or not b or not rid:
            continue
        pk = "|||".join(sorted([
            normalize_entity_for_pair(a),
            normalize_entity_for_pair(b),
        ]))
        if rid not in out[pk]:
            out[pk].append(rid)
    return dict(out)


def _add_within_only_groups(
    entity_meta: dict[str, dict],
    within_group_map: dict,
    registry_map: dict[str, str],
    index_lookup: dict,
    resolver: EntityResolver,
) -> int:
    """Add ethnography groups that have within JR but no cross-group map entity."""
    if not WITHIN_GROUP_XLSX.is_file() and not WITHIN_GROUP_XLSX.with_suffix(".csv").is_file():
        return 0

    df = load_within_group()

    existing_polygon_keys: set[tuple[str, str]] = set()
    existing_polygon_group_ids: set[str] = set()
    for v in entity_meta.values():
        pg = (v.get("polygon_group_id") or "").strip().upper()
        if pg:
            existing_polygon_group_ids.add(pg)
        src = v.get("source", "")
        if src == "murdock":
            mn = (v.get("murdock_name") or "").strip().upper()
            if mn:
                existing_polygon_keys.add(("murdock", mn))
        elif src in ("greg", "geopr"):
            gn = (v.get("greg_name") or "").strip().upper()
            if gn:
                existing_polygon_keys.add((src, gn))

    added = 0
    seen_ethnos: set[str] = set()
    for ethno in df["ethnography_group"].dropna().astype(str).str.strip().unique():
        if not ethno or ethno in seen_ethnos:
            continue
        seen_ethnos.add(ethno)

        pgid = resolve_polygon_id(ethno, registry_map, index_lookup)
        if pgid and pgid in existing_polygon_group_ids:
            continue

        wdata = within_group_map.get(pgid, {"type_i": [], "type_ii": []})
        if not wdata.get("type_i") and not wdata.get("type_ii"):
            continue

        homeland = resolver.resolve_homeland(ethno)
        if homeland is None or not homeland.is_resolved:
            continue

        src = homeland.polygon_source
        if src == "murdock":
            pkey = ("murdock", homeland.polygon_id.upper())
        elif src in ("greg", "geopr"):
            pkey = (src, homeland.polygon_id.upper())
        else:
            pkey = ("point", ethno.upper())

        if pkey[1] and pkey in existing_polygon_keys:
            continue

        entity_key = f"[within] {ethno}"
        resolved = resolver.resolve(ethno)
        entity_meta[entity_key] = homeland_to_entity_meta(
            homeland,
            INTENSITY_COLORS.get(2, "#fcae91"),
            resolved.source if resolved else src,
            polygon_group_id=pgid,
        )
        existing_polygon_keys.add(pkey)
        if pgid:
            existing_polygon_group_ids.add(pgid)
        added += 1

    return added


def _load_between_groups(path: Path) -> pd.DataFrame:
    if path.suffix == ".csv":
        df = pd.read_csv(path, sep=";")
    else:
        df = pd.read_excel(path)
    # Normalise legacy pipeline column names if present
    renames = {}
    if "entity_a_canonical" in df.columns:
        renames["entity_a_canonical"] = "entity_a"
    if "entity_b_canonical" in df.columns:
        renames["entity_b_canonical"] = "entity_b"
    if "regions" in df.columns and "region" not in df.columns:
        renames["regions"] = "region"
    if "ethnography_groups" in df.columns and "ethnography_group" not in df.columns:
        renames["ethnography_groups"] = "ethnography_group"
    if renames:
        df = df.rename(columns=renames)
    if "scope_coded" in df.columns:
        df = df[df["scope_coded"].fillna("between_groups") == "between_groups"].copy()
    return df


def _add_murdock_highlight(
    murdock_highlights: dict,
    murdock_name: str,
    entity_name: str,
    region: str,
    color: str,
    lat: float | None,
    lon: float | None,
) -> None:
    if not murdock_name:
        return
    entry = murdock_highlights[murdock_name]
    if entity_name not in entry["entities"]:
        entry["entities"].append(entity_name)
    entry["n_links"] += 1
    entry["region"] = region or entry["region"]
    entry["color"] = color
    if lat is not None:
        entry["lat"] = lat
    if lon is not None:
        entry["lon"] = lon


def _homeland_from_sheet_columns(
    *,
    name: str,
    prefix: str,
    row: pd.Series,
    resolver: EntityResolver,
    row_region: str,
    entity_region_raw: str,
    effective_region,
) -> tuple[ResolvedEntity | None, EntityHomeland | None]:
    """Use pipeline-resolved homeland columns when manual resolver misses."""
    if _clean_str(row.get(f"{prefix}_homeland_status")) != "resolved":
        return None, None
    psrc = _clean_str(row.get(f"{prefix}_polygon_source")).lower()
    pid = _clean_str(row.get(f"{prefix}_polygon_id"))
    if psrc not in VALID_POLYGON_SOURCES or not pid:
        return None, None
    hit = resolver._lookup_in_source(psrc, pid)
    if hit is None:
        return None, None
    region = effective_region(row_region, entity_region_raw)
    color = REGION_COLORS.get(region, "#e76f51")
    polygon_id = (hit.murdock_name or hit.greg_name or pid).strip()
    resolved = ResolvedEntity(
        raw_name=name,
        canonical=name,
        region=region,
        color=color,
        source=hit.source,
        murdock_name=hit.murdock_name,
        greg_name=hit.greg_name,
        lat=hit.lat,
        lon=hit.lon,
    )
    homeland = EntityHomeland(
        raw_name=name,
        canonical_name=name,
        entity_type="",
        parent_ethnic_group=_clean_str(row.get(f"{prefix}_parent_group")),
        polygon_source=psrc,
        polygon_id=polygon_id,
        region=region,
        lat=hit.lat,
        lon=hit.lon,
    )
    return resolved, homeland


def _add_named_highlight(
    container: dict,
    key: str,
    entity_name: str,
    region: str,
    color: str,
) -> None:
    if not key:
        return
    entry = container[key]
    if entity_name not in entry["entities"]:
        entry["entities"].append(entity_name)
    entry["n_links"] += 1
    entry["region"] = region or entry["region"]
    entry["color"] = color


def _build_highlight_data(
    df: pd.DataFrame,
    resolver: EntityResolver,
    registry_map: dict[str, str],
    index_lookup: dict,
) -> tuple[dict, dict, dict, list, dict, dict, pd.DataFrame]:
    """Highlight homelands for all entities in the between-group dataset."""
    murdock_highlights: dict = defaultdict(lambda: {
        "entities": [], "n_links": 0, "region": "", "color": "#e76f51", "lat": None, "lon": None,
    })
    greg_highlights: dict = defaultdict(lambda: {
        "entities": [], "n_links": 0, "region": "", "color": "#e76f51",
    })
    geopr_highlights: dict = defaultdict(lambda: {
        "entities": [], "n_links": 0, "region": "", "color": "#e76f51",
    })
    markers: list[dict] = []
    entity_meta: dict[str, dict] = {}
    partner_map: dict[str, set[str]] = defaultdict(set)
    cross_pair_types: dict[str, dict[str, str]] = {}
    # Same-ethnic-group pairs from between_groups → type_ii within-group
    same_polygon_within: dict[str, list[dict]] = defaultdict(list)
    _same_polygon_seen: dict[str, set[str]] = defaultdict(set)
    unresolved_rows: list[tuple[str, str, str]] = []
    resolve_cache: dict[str, object] = {}
    homeland_cache: dict[str, EntityHomeland | None] = {}

    def _resolve(name: str):
        if name not in resolve_cache:
            resolve_cache[name] = resolver.resolve(name)
        return resolve_cache[name]

    def _resolve_homeland(name: str) -> EntityHomeland | None:
        if name not in homeland_cache:
            homeland_cache[name] = resolver.resolve_homeland(name)
        return homeland_cache[name]

    def _effective_region(row_region: str, entity_region: str) -> str:
        """Pick the best region string: prefer entity-level GIS region, fall back to
        row-level region (with alias normalisation), then resolver region."""
        for candidate in (entity_region, row_region):
            r = candidate.strip()
            if not r or r.lower() == "nan":
                continue
            if r in REGION_COLORS:
                return r
            mapped = REGION_ALIAS.get(r.lower())
            if mapped:
                return mapped
        return ""

    for _, row in df.iterrows():
        row_region = str(row.get("region", "")).strip()
        if row_region.lower() == "nan":
            row_region = ""

        for prefix in ("entity_a", "entity_b"):
            name = str(row.get(prefix, "")).strip()
            etype = str(row.get(f"{prefix}_type", "")).strip().lower()
            if not name:
                continue

            sheet_status = str(row.get(f"{prefix}_homeland_status", "")).strip()
            entity_region_raw = str(row.get(f"{prefix}_region", "")).strip()
            if entity_region_raw.lower() == "nan":
                entity_region_raw = ""

            resolved = _resolve(name)
            homeland = _resolve_homeland(name)
            if (
                resolved is None
                or resolved.source == "unresolved"
                or not (homeland and homeland.is_resolved)
            ):
                sheet_res, sheet_hom = _homeland_from_sheet_columns(
                    name=name,
                    prefix=prefix,
                    row=row,
                    resolver=resolver,
                    row_region=row_region,
                    entity_region_raw=entity_region_raw,
                    effective_region=_effective_region,
                )
                if sheet_res and sheet_hom:
                    resolved = sheet_res
                    homeland = sheet_hom
                    resolve_cache[name] = resolved
                    homeland_cache[name] = homeland
            region = _effective_region(row_region, entity_region_raw) or (
                homeland.region if homeland else (resolved.region if resolved else "")
            )
            color = REGION_COLORS.get(
                region,
                resolved.color if resolved else "#e76f51",
            )

            if homeland and resolved and resolved.source != "unresolved":
                pgid = resolve_polygon_id(name, registry_map, index_lookup)
                entity_meta[name] = homeland_to_entity_meta(
                    homeland, color, resolved.source, polygon_group_id=pgid,
                )

            if homeland and homeland.polygon_source == "murdock" and homeland.polygon_id:
                _add_murdock_highlight(
                    murdock_highlights,
                    homeland.polygon_id,
                    name,
                    region,
                    color,
                    resolved.lat if resolved else None,
                    resolved.lon if resolved else None,
                )
            elif homeland and homeland.polygon_source == "greg" and homeland.polygon_id:
                _add_named_highlight(
                    greg_highlights,
                    homeland.polygon_id,
                    name,
                    region,
                    color,
                )
            elif homeland and homeland.polygon_source == "geopr" and homeland.polygon_id:
                _add_named_highlight(
                    geopr_highlights,
                    homeland.polygon_id,
                    name,
                    region,
                    color,
                )
            elif resolved and resolved.source != "unresolved" and resolved.lat is not None:
                markers.append({
                    "lat": resolved.lat,
                    "lon": resolved.lon,
                    "color": color,
                    "label": name,
                    "meta": (
                        f"<b>Joking relationship</b><br>{name}<br>"
                        f"Type: {etype}<br>Region: {region or '—'}<br>"
                        f"Source: {resolved.source}"
                    ),
                })
            else:
                unresolved_rows.append((name, etype, sheet_status or "not_found"))

        a = str(row.get("entity_a", "")).strip()
        b = str(row.get("entity_b", "")).strip()
        if a and b and a != b:
            ann_a = {
                "homeland_key": _clean_str(row.get("entity_a_homeland_key", "")),
                "parent_group": _clean_str(row.get("entity_a_parent_group", "")),
            }
            ann_b = {
                "homeland_key": _clean_str(row.get("entity_b_homeland_key", "")),
                "parent_group": _clean_str(row.get("entity_b_parent_group", "")),
            }
            ha = _resolve_homeland(a)
            hb = _resolve_homeland(b)
            same = same_ethnic_from_annotations(ann_a, ann_b) or (
                ha and hb and same_ethnic_group(ha, hb)
            )
            if same and ha:
                gkey = _polygon_key_from_homeland(ha, registry_map)
                pair_key = "|||".join(sorted([a, b]))
                if pair_key not in _same_polygon_seen[gkey]:
                    _same_polygon_seen[gkey].add(pair_key)
                    same_polygon_within[gkey].append({"a": a, "b": b})
            else:
                partner_map[a].add(b)
                partner_map[b].add(a)
                pair_key = "|||".join(sorted([a, b]))
                if pair_key not in cross_pair_types:
                    cross_pair_types[pair_key] = {
                        a: _clean_str(row.get("entity_a_type", "")),
                        b: _clean_str(row.get("entity_b_type", "")),
                    }

    # Deduplicate marker labels
    seen_labels = set()
    unique_markers = []
    for m in markers:
        if m["label"] in seen_labels:
            continue
        seen_labels.add(m["label"])
        unique_markers.append(m)

    unresolved_df = pd.DataFrame(
        unresolved_rows, columns=["entity", "entity_type", "homeland_status"],
    ).drop_duplicates()
    partner_map_json = {k: sorted(v) for k, v in partner_map.items()}
    return (
        dict(murdock_highlights),
        dict(greg_highlights),
        dict(geopr_highlights),
        unique_markers,
        entity_meta,
        partner_map_json,
        cross_pair_types,
        dict(same_polygon_within),
        unresolved_df,
    )


def _compute_group_intensity(
    entity_meta: dict,
    partner_map: dict,
    within_group_map: dict,
) -> dict[str, dict]:
    """Pre-compute JR counts per polygon_id group."""
    visual_groups: dict[str, list[str]] = defaultdict(list)
    for entity_name, meta in entity_meta.items():
        vkey = _visual_map_key(entity_name, meta)
        visual_groups[vkey].append(entity_name)

    result: dict[str, dict] = {}

    def _aggregate(vkey: str, entities: list[str]) -> dict:
        polygon_ids: set[str] = set()
        for e in entities:
            meta = entity_meta[e]
            pg = (meta.get("polygon_group_id") or "").strip().upper()
            if pg:
                polygon_ids.add(pg)

        seen_within: set[str] = set()
        n_i = n_ii = 0
        for pid in polygon_ids:
            wdata = within_group_map.get(pid, {"type_i": [], "type_ii": []})
            for p in wdata.get("type_i", []):
                pk = "|||".join(sorted([p["a"], p["b"]]))
                if pk not in seen_within:
                    seen_within.add(pk)
                    n_i += 1
            for p in wdata.get("type_ii", []):
                pk = "|||".join(sorted([p["a"], p["b"]]))
                if pk not in seen_within:
                    seen_within.add(pk)
                    n_ii += 1

        seen_cross: set[str] = set()
        for e in entities:
            for p in partner_map.get(e, []):
                seen_cross.add("|||".join(sorted([e, p])))
        n_iii = len(seen_cross)

        n_types = sum([n_i > 0, n_ii > 0, n_iii > 0])
        if   n_types == 0:  intensity = 0
        elif n_types == 3:  intensity = 5
        elif n_types == 2:  intensity = 4
        elif n_iii > 0:     intensity = 3
        elif n_ii  > 0:     intensity = 2
        else:               intensity = 1

        return {
            "n_i": n_i, "n_ii": n_ii, "n_iii": n_iii,
            "intensity": intensity,
            "color": INTENSITY_COLORS.get(intensity, "#ccc"),
        }

    for vkey, entities in visual_groups.items():
        result[vkey] = _aggregate(vkey, entities)

    return result


def _apply_registry_map_placement(
    entity_meta: dict[str, dict],
    registry_df: pd.DataFrame,
    resolver: EntityResolver,
) -> None:
    """Use registry polygon_source for map placement when an entity resolved to a fallback layer."""
    reg_by_id = {
        str(r["polygon_id"]).strip().upper(): r
        for _, r in registry_df.iterrows()
        if _clean_str(r.get("polygon_id"))
    }
    canonical: dict[str, EntityHomeland] = {}
    for pgid, row in reg_by_id.items():
        for label in (_clean_str(row.get("display_name")), pgid.title()):
            if not label:
                continue
            h = resolver.resolve_homeland(label)
            if h and h.is_resolved:
                canonical[pgid] = h
                break

    for name, meta in entity_meta.items():
        pgid = (meta.get("polygon_group_id") or "").strip().upper()
        if not pgid or pgid not in canonical:
            continue
        reg = reg_by_id.get(pgid, {})
        preferred = _clean_str(reg.get("polygon_source")).lower() or canonical[pgid].polygon_source
        current = (meta.get("polygon_source") or meta.get("source") or "").lower()
        if SOURCE_PRIORITY.get(current, 99) <= SOURCE_PRIORITY.get(preferred, 99):
            continue
        h = canonical[pgid]
        entity_meta[name] = homeland_to_entity_meta(
            h,
            meta.get("color", "#888"),
            preferred,
            polygon_group_id=pgid,
        )


def build_map(input_path: Path, output_path: Path) -> None:
    if not JR_RECORDS_JSON.is_file():
        print(f"Missing JR records: {JR_RECORDS_JSON}")
        print("Run first: uv run python code/visualization/prepare.py data")
        sys.exit(1)

    with JR_RECORDS_JSON.open(encoding="utf-8") as handle:
        jr_records = json.load(handle)

    print(f"Loading joking data: {input_path}")
    df = _load_between_groups(input_path)
    print(f"  {len(df)} cross-group relationship rows · {len(jr_records)} detail records")

    print("Resolving entities to homelands…")
    if not POLYGON_GROUP_REGISTRY_XLSX.is_file():
        print(f"  Creating {POLYGON_GROUP_REGISTRY_XLSX.name} from entity index (edit aliases manually)…")
        save_registry(bootstrap_from_entity_index())

    registry_df = load_registry()
    registry_map = build_name_to_polygon_map(registry_df)
    index_lookup = build_lookup(load_index())
    resolver = EntityResolver()
    highlights, greg_highlights, geopr_highlights, markers, entity_meta, partner_map, cross_pair_types, same_poly_within, unresolved = _build_highlight_data(
        df, resolver, registry_map, index_lookup,
    )
    cross_pair_records = _build_cross_pair_records(df)
    print(f"  Murdock polygons highlighted: {len(highlights)}")
    print(f"  GREG polygons highlighted:    {len(greg_highlights)}")
    print(f"  GeoEPR polygons highlighted:  {len(geopr_highlights)}")
    print(f"  Point markers (no polygon):   {len(markers)}")
    print(f"  Unresolved entities:        {len(unresolved)} (see RA_workpack)")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    between_names = {
        *df["entity_a"].dropna().astype(str),
        *df["entity_b"].dropna().astype(str),
    }
    unmapped = collect_unmapped_names(registry_map, index_lookup, between_entity_names=between_names)
    if unmapped:
        print(f"  Unmapped registry names: {len(unmapped)} (add aliases in polygon_group_registry if needed)")

    for stale in (
        UNRESOLVED_CSV,
        UNMAPPED_REGISTRY_CSV,
        OUTPUT_DIR / "cross_group_jr_map.html",
    ):
        if stale.is_file():
            stale.unlink()
            print(f"  removed obsolete {stale.name}")

    print("Building GeoJSON layers…")
    murdock_gj = murdock_geojson()
    greg_gj = greg_geojson()
    geoepr_gj = geoepr_geojson()

    unique_entities = len({
        *df["entity_a"].dropna().astype(str),
        *df["entity_b"].dropna().astype(str),
    })
    n_keerthana = sum(1 for r in jr_records.values() if r.get("source") == "Keerthana")
    n_ehraf = sum(1 for r in jr_records.values() if r.get("source") == "eHRAF")
    n_icmid = sum(1 for r in jr_records.values() if r.get("source") == "ICMID")
    scope_counts: dict[str, int] = {}
    for r in jr_records.values():
        sc = str(r.get("scope_coded") or "").strip().lower().replace("-", "_")
        if sc in ("between_groups",):
            sc = "cross_group"
        if sc:
            scope_counts[sc] = scope_counts.get(sc, 0) + 1
    n_cross = scope_counts.get("cross_group", len(df))
    n_within = scope_counts.get("within_group", 0)
    n_kin = scope_counts.get("kinship", 0)
    stats_line = (
        f"{n_cross} cross · {n_within} within · {n_kin} kin · "
        f"{unique_entities} cross entities · "
        f"{len(highlights)} Murdock + {len(greg_highlights)} GREG + {len(geopr_highlights)} GeoEPR · "
        f"{len(jr_records)} JR records ({n_ehraf} eHRAF · {n_keerthana} Keerthana · {n_icmid} ICMID)"
    )

    # Build within-group pair map (keyed by polygon_id)
    print("  Building within-group pair map…")
    within_group_map, within_pair_records = _build_within_group_map(registry_map, index_lookup)

    # Merge same-ethnic-group pairs from cross_group_map into within_group_map
    merged_count = 0
    for mkey, pairs in same_poly_within.items():
        pid = resolve_polygon_id(mkey, registry_map, index_lookup) if mkey else mkey
        if pid not in within_group_map:
            within_group_map[pid] = {"type_i": [], "type_ii": []}
        existing_pairs = {
            "|||".join(sorted([p["a"], p["b"]]))
            for p in within_group_map[pid]["type_ii"]
        }
        for pair in pairs:
            pk = "|||".join(sorted([pair["a"], pair["b"]]))
            if pk not in existing_pairs:
                within_group_map[pid]["type_ii"].append({**pair, "record_ids": []})
                existing_pairs.add(pk)
                merged_count += 1
    if merged_count:
        print(f"  Merged {merged_count} same-polygon pairs into within_group_map")

    # ── Pre-compute accurate group-level intensity (used for colors + display) ──
    group_intensity = _compute_group_intensity(entity_meta, partner_map, within_group_map)
    print(f"  Group intensity computed: {len(group_intensity)} groups")

    # Save as CSV for easy inspection
    gi_csv = OUTPUT_DIR / "group_intensity_summary.csv"
    gi_csv.parent.mkdir(parents=True, exist_ok=True)
    gi_rows = sorted(
        [{"group": k, **v} for k, v in group_intensity.items()],
        key=lambda r: (-r["intensity"], r["group"]),
    )
    pd.DataFrame(gi_rows).to_csv(gi_csv, index=False)
    print(f"  Saved group intensity summary → {gi_csv}")

    added_within_only = _add_within_only_groups(
        entity_meta, within_group_map, registry_map, index_lookup, resolver,
    )
    print(f"  Within-only groups added to map: {added_within_only}")

    _apply_registry_map_placement(entity_meta, registry_df, resolver)

    type_labels = [
        ("kin", "Kinship (within-kin)", INTENSITY_COLORS[1]),
        ("within", "Within-group", INTENSITY_COLORS[2]),
        ("cross", "Cross-group", INTENSITY_COLORS[3]),
    ]
    intensity_legend = "\n".join(
        f'<label class="lr lr-type-filter" data-type="{key}">'
        f'<input type="checkbox" class="type-filter-cb" value="{key}" '
        f'onchange="toggleTypeFilter(\'{key}\', this.checked)">'
        f'<div class="ls" style="background:{color}"></div>'
        f'<span>{label}</span></label>'
        for key, label, color in type_labels
    )
    intensity_legend += (
        '\n<div id="intensity-filter-hint" class="intensity-hint"></div>'
        '\n<div class="lr" style="margin-top:4px;color:#999;font-size:9px;font-style:italic;line-height:1.3">'
        'Checked = must have</div>'
    )

    html = _render_map_html(
        stats_line=stats_line,
        intensity_legend=intensity_legend,
        murdock_gj=murdock_gj,
        greg_gj=greg_gj,
        geoepr_gj=geoepr_gj,
        entity_meta=entity_meta,
        partner_map=partner_map,
        cross_pair_types=cross_pair_types,
        region_colors=REGION_COLORS,
        intensity_colors=INTENSITY_COLORS,
        within_group_map=within_group_map,
        group_intensity=group_intensity,
        jr_records=jr_records,
        cross_pair_records=cross_pair_records,
        within_pair_records=within_pair_records,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"\nWrote map → {output_path}  ({len(html):,} bytes)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build JR homeland map (cross + within + kin)")
    parser.add_argument(
        "--input",
        type=Path,
        default=CROSS_GROUP_MAP_XLSX,
        help="Cross-group map table (default: output/jr_database/cross_group_map.xlsx)",
    )
    parser.add_argument("--output", type=Path, default=CROSS_GROUP_MAP_HTML)
    args = parser.parse_args()

    if not args.input.is_file():
        print(f"Missing input file: {args.input}")
        print("Run first: uv run python code/visualization/prepare.py data")
        sys.exit(1)

    build_map(args.input, args.output)


if __name__ == "__main__":
    main()

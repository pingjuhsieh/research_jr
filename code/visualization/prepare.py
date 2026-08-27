#!/usr/bin/env python3
"""
Data preparation for the JR map pipeline.

Subcommands:
    data       Maintain ethnic_entity_index.xlsx + cross_group_map.xlsx
    intensity  Compute ethnic_group_jr_summary.xlsx
    all        Run data then intensity (default)

First-time setup:
    uv run python code/visualization/prepare.py data --import-keerthana
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

_VIS_DIR = Path(__file__).resolve().parent
if str(_VIS_DIR) not in sys.path:
    sys.path.insert(0, str(_VIS_DIR))

import pandas as pd

from config import (
    CROSS_GROUP_MAP_XLSX,
    BETWEEN_GROUP_SOURCE_MERGED_XLSX,
    BETWEEN_GROUP_SOURCE_XLSX,
    DOC_LEVEL_JR_CSV,
    ETHNIC_ENTITY_INDEX_XLSX,
    JR_SUMMARY_XLSX,
    KEERTHANA_ETHNICS_XLSX,
    KEERTHANA_JOKING_XLSX,
    LOOKUP_ROOT,
    POLYGON_GROUP_REGISTRY_XLSX,
    REGION_ALIAS,
    REGION_COLORS,
    UNMATCHED_HOMELANDS_XLSX,
    WITHIN_GROUP_XLSX,
)
from jr_tables import load_cross_group_map, load_within_group, save_cross_group_map
from entity_homeland import (
    classify_within_entity_types,
    compute_intensity,
    same_ethnic_from_annotations,
)
from entity_index import (
    annotate_entity,
    bootstrap_from_keerthana,
    build_lookup,
    collect_index_candidates,
    compute_homeland_found,
    export_unmatched_homelands,
    group_map_key_from_row,
    homeland_key_from_row,
    load_index,
    lookup_row,
    prune_index_stubs,
    scrub_legacy_auto_guesses,
    save_index,
    sync_new_entities,
)
from entity_resolver import EntityResolver
from polygon_registry import (
    bootstrap_from_entity_index,
    load_registry,
    remove_auto_bootstrapped_registry_rows,
    save_registry,
    scrub_subgroup_aliases,
)
from merge_sources import write_merged_sources, _norm_record_id


def _clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _truncate(s: str, max_len: int = 500) -> str:
    s = _clean(s)
    return s if len(s) <= max_len else s[: max_len - 3] + "..."


def _norm_region(r: str) -> str:
    if r in REGION_COLORS:
        return r
    return REGION_ALIAS.get(r.lower(), r)


def _joking_source_path() -> Path:
    if BETWEEN_GROUP_SOURCE_MERGED_XLSX.is_file():
        return BETWEEN_GROUP_SOURCE_MERGED_XLSX
    if BETWEEN_GROUP_SOURCE_XLSX.is_file():
        return BETWEEN_GROUP_SOURCE_XLSX
    return KEERTHANA_JOKING_XLSX


def _prepare_cross_group_map(lookup: dict) -> pd.DataFrame:
    src = _joking_source_path()
    raw = pd.read_excel(src)
    rows = []
    for idx, r in raw.iterrows():
        entity_a = _clean(r.get("entity_a"))
        entity_b = _clean(r.get("entity_b"))
        if not entity_a or not entity_b or entity_a == entity_b:
            continue
        joking_source = _clean(r.get("joking_source")) or "unknown"
        rid = _norm_record_id(r.get("relationship_row_id"))
        if not rid and joking_source != "ehraf_v2":
            rid = f"keerthana:cross:{idx}"
        ann_a = annotate_entity(lookup, entity_a, _clean(r.get("ethnography_groups", "")))
        ann_b = annotate_entity(lookup, entity_b, _clean(r.get("ethnography_groups", "")))
        rows.append({
            "relationship_row_id": rid,
            "entity_a": entity_a,
            "entity_a_type": _clean(r.get("entity_a_type")),
            "entity_b": entity_b,
            "entity_b_type": _clean(r.get("entity_b_type")),
            "region": _clean(r.get("regions")),
            "ethnography_group": _clean(r.get("ethnography_groups")),
            "relation_type": _clean(r.get("relation_types_coded")),
            "relation_category": _clean(r.get("relation_categories")),
            "symmetry": _clean(r.get("symmetry")),
            "joking_source": _clean(r.get("joking_source")) or "unknown",
            "notes": _truncate(r.get("notes"), 500),
            "entity_a_homeland_status": ann_a["homeland_status"],
            "entity_a_polygon_source": ann_a["polygon_source"],
            "entity_a_polygon_id": ann_a["polygon_id"],
            "entity_a_parent_group": ann_a["parent_group"],
            "entity_a_homeland_key": ann_a["homeland_key"],
            "entity_a_region": ann_a["region"],
            "entity_b_homeland_status": ann_b["homeland_status"],
            "entity_b_polygon_source": ann_b["polygon_source"],
            "entity_b_polygon_id": ann_b["polygon_id"],
            "entity_b_parent_group": ann_b["parent_group"],
            "entity_b_homeland_key": ann_b["homeland_key"],
            "entity_b_region": ann_b["region"],
        })
    return pd.DataFrame(rows)


def cmd_data(import_keerthana: bool = False) -> None:
    LOOKUP_ROOT.mkdir(parents=True, exist_ok=True)
    BETWEEN_GROUP_SOURCE_XLSX.parent.mkdir(parents=True, exist_ok=True)
    CROSS_GROUP_MAP_XLSX.parent.mkdir(parents=True, exist_ok=True)

    if import_keerthana:
        print(f"Importing entity index from {KEERTHANA_ETHNICS_XLSX.name}…")
        if not KEERTHANA_ETHNICS_XLSX.is_file():
            print(f"ERROR: not found: {KEERTHANA_ETHNICS_XLSX}")
            sys.exit(1)
        df = bootstrap_from_keerthana()
        save_index(df)
        print(f"  → {ETHNIC_ENTITY_INDEX_XLSX}  ({len(df)} rows)")
        if KEERTHANA_JOKING_XLSX.is_file() and not BETWEEN_GROUP_SOURCE_XLSX.is_file():
            shutil.copy2(KEERTHANA_JOKING_XLSX, BETWEEN_GROUP_SOURCE_XLSX)
            print(f"  Copied joking source → {BETWEEN_GROUP_SOURCE_XLSX}")
        print("Edit ethnic_entity_index.xlsx, then run: prepare.py data")
        return

    index_df = load_index()
    if index_df.empty:
        print(f"No entity index at {ETHNIC_ENTITY_INDEX_XLSX}")
        print("Run first:  uv run python code/visualization/prepare.py data --import-keerthana")
        sys.exit(1)

    joking_path = _joking_source_path()
    if not joking_path.is_file():
        if not BETWEEN_GROUP_SOURCE_XLSX.is_file():
            print(f"ERROR: joking source not found: {joking_path}")
            sys.exit(1)
        if not DOC_LEVEL_JR_CSV.is_file():
            print(f"ERROR: v2 export not found: {DOC_LEVEL_JR_CSV}")
            print("Run: uv run python code/llm_ehraf/run.py extract && uv run python code/llm_ehraf/run.py export")
            sys.exit(1)

    if not import_keerthana:
        print("Building merged Keerthana + v2 eHRAF sources…")
        write_merged_sources()
        joking_path = BETWEEN_GROUP_SOURCE_MERGED_XLSX

    if not joking_path.is_file():
        print(f"ERROR: joking source not found: {joking_path}")
        sys.exit(1)

    print(f"Entity index: {len(index_df)} rows")
    index_df, n_pruned = prune_index_stubs(index_df)
    if n_pruned:
        print(f"  Pruned {n_pruned} non-indexable stub(s)")

    candidates = collect_index_candidates(joking_path, WITHIN_GROUP_XLSX)
    index_df, n_new = sync_new_entities(index_df, candidates)
    if n_new:
        print(f"  Added {n_new} new indexable entity stub(s)")

    index_df, n_scrubbed = scrub_legacy_auto_guesses(index_df)
    if n_scrubbed:
        print(f"  Scrubbed {n_scrubbed} legacy auto-guess row(s) from entity index")

    print("  Checking homeland mappings (manual only)…")
    resolver = EntityResolver()
    unmatched_df = export_unmatched_homelands(index_df, resolver)
    UNMATCHED_HOMELANDS_XLSX.parent.mkdir(parents=True, exist_ok=True)
    unmatched_df.to_excel(UNMATCHED_HOMELANDS_XLSX, index=False, sheet_name="unmatched")
    print(f"  → {UNMATCHED_HOMELANDS_XLSX}  ({len(unmatched_df)} row(s) need manual review)")

    save_index(index_df)
    n_missing = (~index_df.apply(compute_homeland_found, axis=1)).sum()
    print(f"  → {ETHNIC_ENTITY_INDEX_XLSX}  ({len(index_df)} rows, {n_missing} without homeland in index)")

    if not POLYGON_GROUP_REGISTRY_XLSX.is_file():
        print(f"Creating {POLYGON_GROUP_REGISTRY_XLSX.name} from entity index…")
        save_registry(bootstrap_from_entity_index())
        print(f"  → {POLYGON_GROUP_REGISTRY_XLSX}  (edit aliases column manually)")
    else:
        registry_df = scrub_subgroup_aliases(load_registry(), index_df)
        registry_df, n_rm = remove_auto_bootstrapped_registry_rows(registry_df)
        if n_rm:
            print(f"  Removed {n_rm} auto-bootstrapped geopr/joshua registry row(s)")
        save_registry(registry_df)
        print(f"Polygon registry: {len(registry_df)} groups")

    lookup = build_lookup(index_df)
    print(f"Building cross_group_map from {joking_path.name}…")
    joking_df = _prepare_cross_group_map(lookup)
    save_cross_group_map(joking_df)
    n_bad = (
        joking_df["entity_a_homeland_status"].isin(("not_found", "not_in_index"))
        | joking_df["entity_b_homeland_status"].isin(("not_found", "not_in_index"))
    ).sum()
    print(f"  → {CROSS_GROUP_MAP_XLSX}  ({len(joking_df)} rows, {n_bad} unresolved endpoints)")


def cmd_intensity() -> None:
    JR_SUMMARY_XLSX.parent.mkdir(parents=True, exist_ok=True)
    if not CROSS_GROUP_MAP_XLSX.is_file():
        print(f"Missing {CROSS_GROUP_MAP_XLSX} — run: prepare.py data")
        sys.exit(1)

    print("Loading data sources…")
    df_within = load_within_group()
    df_within = df_within[df_within["ethnography_group"].fillna("").astype(str).str.strip() != ""]
    df_between = load_cross_group_map()
    lookup = build_lookup(pd.read_excel(ETHNIC_ENTITY_INDEX_XLSX))

    counts: dict[str, dict] = {}

    def get_or_create(homeland_key, display_group, group_map_key, polygon_source, polygon_id, region):
        if homeland_key not in counts:
            counts[homeland_key] = {
                "homeland_key": homeland_key, "display_group": display_group,
                "group_map_key": group_map_key, "polygon_source": polygon_source,
                "polygon_id": polygon_id, "region": region,
                "type_i": 0, "type_ii": 0, "type_iii": 0,
            }
        e = counts[homeland_key]
        if display_group and (not e["display_group"] or e["display_group"] == homeland_key):
            e["display_group"] = display_group
        if region and not e["region"]:
            e["region"] = region
        return e

    def entry_from_ethnography(ethno: str, fallback_region: str = "") -> dict:
        row = lookup_row(lookup, ethno)
        if row is not None:
            return get_or_create(
                homeland_key_from_row(row),
                _clean(row.get("parent_ethnic_group")) or _clean(row.get("canonical_name")) or ethno,
                group_map_key_from_row(row),
                _clean(row["polygon_source"]), _clean(row["polygon_id"]),
                _norm_region(_clean(row["region"]) or fallback_region),
            )
        return get_or_create(f"entity:{ethno.upper()}", ethno, ethno.upper(), "", "",
                             _norm_region(fallback_region))

    print(f"Processing within_groups ({len(df_within)} rows)…")
    for _, row in df_within.iterrows():
        ethno = _clean(row.get("ethnography_group", ""))
        if not ethno:
            continue
        entry = entry_from_ethnography(ethno, _clean(row.get("region", "")))
        jtype = classify_within_entity_types(_clean(row.get("entity_a_type")), _clean(row.get("entity_b_type")))
        if jtype == "type_i":
            entry["type_i"] += 1
        elif jtype == "type_ii":
            entry["type_ii"] += 1

    print(f"Processing between_groups ({len(df_between)} rows)…")
    seen: set[tuple[str, str]] = set()
    for _, row in df_between.iterrows():
        a, b = _clean(row.get("entity_a")), _clean(row.get("entity_b"))
        if not a or not b:
            continue
        pk = tuple(sorted([a, b]))
        if pk in seen:
            continue
        seen.add(pk)

        def _ann(prefix):
            return {
                "polygon_source": _clean(row.get(f"{prefix}_polygon_source")),
                "polygon_id": _clean(row.get(f"{prefix}_polygon_id")),
                "parent_group": _clean(row.get(f"{prefix}_parent_group")),
                "homeland_key": _clean(row.get(f"{prefix}_homeland_key")),
                "region": _norm_region(_clean(row.get(f"{prefix}_region"))),
            }

        ann_a, ann_b = _ann("entity_a"), _ann("entity_b")
        row_a, row_b = lookup_row(lookup, a), lookup_row(lookup, b)

        def _entry(name, ann, idx_row):
            hk = ann["homeland_key"] or (homeland_key_from_row(idx_row) if idx_row is not None else f"entity:{name.upper()}")
            gmk = group_map_key_from_row(idx_row) if idx_row is not None else name.upper()
            disp = _clean(idx_row.get("parent_ethnic_group")) if idx_row is not None else name
            if idx_row is not None and not disp:
                disp = _clean(idx_row.get("canonical_name")) or name
            return get_or_create(hk, disp or name, gmk, ann["polygon_source"], ann["polygon_id"], ann["region"])

        if same_ethnic_from_annotations(ann_a, ann_b):
            _entry(a, ann_a, row_a)["type_ii"] += 1
        else:
            if ann_a["homeland_key"] or ann_a["polygon_id"] or row_a is not None:
                _entry(a, ann_a, row_a)["type_iii"] += 1
            if ann_b["homeland_key"] or ann_b["polygon_id"] or row_b is not None:
                _entry(b, ann_b, row_b)["type_iii"] += 1

    rows = []
    for e in counts.values():
        n_i, n_ii, n_iii = e["type_i"], e["type_ii"], e["type_iii"]
        rows.append({
            "homeland_key": e["homeland_key"], "display_group": e["display_group"],
            "group_map_key": e["group_map_key"], "polygon_source": e["polygon_source"],
            "polygon_id": e["polygon_id"], "region": e["region"],
            "type_i_count": n_i, "type_ii_count": n_ii, "type_iii_count": n_iii,
            "n_types": sum([n_i > 0, n_ii > 0, n_iii > 0]),
            "intensity": compute_intensity(n_i, n_ii, n_iii),
        })

    df_out = pd.DataFrame(rows).sort_values(["intensity", "display_group"], ascending=[False, True])
    df_out.to_excel(JR_SUMMARY_XLSX, index=False, sheet_name="jr_summary")
    print(f"  → {JR_SUMMARY_XLSX}  ({len(df_out)} groups)")


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare JR map data")
    sub = parser.add_subparsers(dest="command")

    p_data = sub.add_parser("data", help="Maintain entity index + between-group table")
    p_data.add_argument("--import-keerthana", action="store_true")
    sub.add_parser("intensity", help="Compute JR intensity summary")
    sub.add_parser("all", help="Run data + intensity")

    args = parser.parse_args()
    cmd = args.command or "all"

    if cmd == "data":
        cmd_data(import_keerthana=getattr(args, "import_keerthana", False))
    elif cmd == "intensity":
        cmd_intensity()
    elif cmd == "all":
        cmd_data()
        print()
        cmd_intensity()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()

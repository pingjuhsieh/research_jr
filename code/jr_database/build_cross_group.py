#!/usr/bin/env python3
"""Build consolidated cross-group JR database with homeland mapping.

Workflow (manual homeland fixes):
  1. export_ra_workpack.py → output/jr_database/RA_workpack.xlsx
  2. Fill sheet 1_unmatched_entities (polygon_source, polygon_id, …)
  3. uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
  4. Re-run export_ra_workpack.py

You normally only edit RA_workpack.xlsx. Apply writes into
ethnic_entity_index.xlsx (the cumulative manual store). polygon_group_registry
is auto-synced — you do not need to maintain it for JR resolve.

Usage (from ICMID PingJu project root):
    uv run python -B code/jr_database/build_cross_group.py
    uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
    bash code/jr_database/scripts/run.sh              # build + map
    bash code/jr_database/scripts/run.sh --no-map     # build only
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd

_CODE = Path(__file__).resolve().parent.parent
_PIPELINE = _CODE.parent
for _p in (_CODE, _PIPELINE, _CODE / "visualization"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from entity_index import INDEX_COLUMNS, load_index, save_index  # noqa: E402
from polygon_registry import (  # noqa: E402
    REGISTRY_COLUMNS,
    load_registry,
    normalize_registry,
    save_registry,
)

from jr_database.config import (  # noqa: E402
    ASSERTIONS_CSV,
    CROSS_GROUP_CSV,
    CROSS_GROUP_XLSX,
    ETHNIC_ENTITY_INDEX_XLSX,
    ICMID_MANUAL_XLSX,
    ICMID_UNMATCHED_SHEET,
    POLYGON_GROUP_REGISTRY_XLSX,
    RA_UNMATCHED_SHEET,
    RA_WORKPACK_XLSX,
    ensure_output_dirs,
)
from jr_database.lib.sync_icmid_unmatched import sync_icmid_unmatched_sheet  # noqa: E402
from jr_database.resolve_homeland import VALID_HOMELAND, get_resolver  # noqa: E402
from jr_database.sources import load_all_cross_assertions  # noqa: E402

# Columns the reviewer fills in RA_workpack.xlsx / 1_unmatched_entities
UNMATCHED_FILL_COLS = (
    "polygon_source",
    "polygon_id",
    "display_name",
    "resolve_source",
    "coder",
    "aliases",
    "notes",
)


def _clean(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" else s


def _resolve_source_from_row(r) -> str:
    """Prefer resolve_source; accept legacy/custom column name `source`."""
    return _clean(r.get("resolve_source")) or _clean(r.get("source"))


_ILLEGAL_XLSX_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _excel_safe(val: str) -> str:
    return _ILLEGAL_XLSX_RE.sub("", val)


def _split_aliases(val: str) -> list[str]:
    return [a.strip() for a in _clean(val).replace(";", ",").split(",") if a.strip()]


def _upsert_index_row(
    index: pd.DataFrame,
    *,
    raw: str,
    src: str,
    pid: str,
    display_name: str,
    resolve_source: str,
    coder: str,
    notes: str,
) -> pd.DataFrame:
    key = raw.upper()
    mask = index["raw_value"].astype(str).str.strip().str.upper() == key
    if mask.any():
        index.loc[mask, "polygon_source"] = src
        index.loc[mask, "polygon_id"] = pid
        if display_name:
            index.loc[mask, "canonical_name"] = display_name
        if resolve_source:
            index.loc[mask, "resolve_source"] = resolve_source
        if coder:
            index.loc[mask, "coder"] = coder
        if notes:
            prev = index.loc[mask, "notes"].map(_clean)
            index.loc[mask, "notes"] = [
                notes if not p else (p if notes in p else f"{p}; {notes}")
                for p in prev
            ]
        return index

    row = {c: "" for c in INDEX_COLUMNS}
    row.update(
        {
            "raw_value": raw,
            "canonical_name": display_name or raw,
            "polygon_source": src,
            "polygon_id": pid,
            "resolve_source": resolve_source,
            "coder": coder,
            "notes": notes or "filled via RA_workpack",
        }
    )
    return pd.concat([index, pd.DataFrame([row])], ignore_index=True)


def sync_registry_from_index(index: pd.DataFrame) -> int:
    """Ensure registry has a row for every trusted index polygon; keep manual aliases."""
    registry = load_registry() if POLYGON_GROUP_REGISTRY_XLSX.is_file() else pd.DataFrame(columns=REGISTRY_COLUMNS)
    by_id = {
        _clean(r["polygon_id"]).upper(): r.to_dict()
        for _, r in registry.iterrows()
        if _clean(r.get("polygon_id"))
    }
    added = 0
    for _, row in index.iterrows():
        src = _clean(row.get("polygon_source")).lower().replace("geoepr", "geopr")
        pid = _clean(row.get("polygon_id")).upper()
        if src not in VALID_HOMELAND or not pid:
            continue
        if pid in by_id:
            # Prefer murdock if index says murdock and registry has weaker source
            existing_src = _clean(by_id[pid].get("polygon_source")).lower()
            if src == "murdock" and existing_src != "murdock":
                by_id[pid]["polygon_source"] = "murdock"
            continue
        by_id[pid] = {
            "polygon_id": pid,
            "polygon_source": src,
            "display_name": _clean(row.get("canonical_name")) or pid.title(),
            "aliases": "",
            "region": _clean(row.get("region")),
            "notes": "synced from ethnic_entity_index",
        }
        added += 1

    out = normalize_registry(pd.DataFrame(by_id.values())) if by_id else pd.DataFrame(columns=REGISTRY_COLUMNS)
    save_registry(out)
    return added


def apply_unmatched(
    path: Path = RA_WORKPACK_XLSX,
    sheet: str = RA_UNMATCHED_SHEET,
) -> int:
    """Write filled unmatched rows into ethnic_entity_index.xlsx and sync registry."""
    if not path.is_file():
        raise FileNotFoundError(f"No RA workpack: {path}")
    try:
        um = pd.read_excel(path, sheet_name=sheet)
    except ValueError as exc:
        raise FileNotFoundError(f"Missing sheet {sheet!r} in {path}") from exc
    if um.empty:
        print("unmatched sheet empty — nothing to apply")
        return 0

    index = load_index() if ETHNIC_ENTITY_INDEX_XLSX.is_file() else pd.DataFrame(columns=INDEX_COLUMNS)
    applied = 0
    alias_n = 0

    for _, r in um.iterrows():
        src = _clean(r.get("polygon_source")).lower().replace("geoepr", "geopr")
        pid = _clean(r.get("polygon_id")).upper()
        if src not in VALID_HOMELAND or not pid:
            continue
        raw = _clean(r.get("entity"))
        if not raw:
            continue

        display = _clean(r.get("display_name"))
        resolve_source = _resolve_source_from_row(r)
        coder = _clean(r.get("coder"))
        notes = _clean(r.get("notes"))
        index = _upsert_index_row(
            index,
            raw=raw,
            src=src,
            pid=pid,
            display_name=display,
            resolve_source=resolve_source,
            coder=coder,
            notes=notes,
        )
        applied += 1

        for alias in _split_aliases(r.get("aliases", "")):
            if alias.upper() == raw.upper():
                continue
            index = _upsert_index_row(
                index,
                raw=alias,
                src=src,
                pid=pid,
                display_name=display or alias,
                resolve_source=resolve_source,
                coder=coder,
                notes=notes or f"alias of {raw}",
            )
            alias_n += 1

    save_index(index)
    reg_added = sync_registry_from_index(index)
    print(f"Applied {applied} entity fills (+{alias_n} aliases) → {ETHNIC_ENTITY_INDEX_XLSX}")
    print(f"Registry sync: +{reg_added} new polygon rows → {POLYGON_GROUP_REGISTRY_XLSX}")
    return applied


def build_pair_table(assertions: pd.DataFrame) -> pd.DataFrame:
    resolver = get_resolver()
    groups = assertions.groupby("pair_key", sort=True)
    rows: list[dict] = []

    for pk, g in groups:
        a = g.iloc[0]["entity_a"]
        b = g.iloc[0]["entity_b"]
        if a.casefold() > b.casefold():
            a, b = b, a

        sources = sorted({_clean(s) for s in g["source_dataset"] if _clean(s)})
        needs_review = int((g["needs_review"].fillna(0).astype(int) > 0).all())

        regions = [_clean(x) for x in g["region"] if _clean(x)]
        notes_bits = [_clean(x) for x in g["notes"] if _clean(x)]

        source_bits: list[str] = []
        for _, ar in g.iterrows():
            bit = (
                _clean(ar.get("doc_id"))
                or _clean(ar.get("source_url"))
                or _clean(ar.get("source_citation"))
            )
            if bit and bit not in source_bits:
                source_bits.append(bit)

        quote_bits: list[str] = []
        for q in g["quote"]:
            q = _clean(q)
            if q and q not in quote_bits:
                quote_bits.append(q)

        ha = resolver.resolve(a)
        hb = resolver.resolve(b)
        complete = int(ha.polygon_source in VALID_HOMELAND and hb.polygon_source in VALID_HOMELAND)

        rows.append(
            {
                "entity_a": a,
                "entity_b": b,
                "source_flags": ";".join(sources),
                "n_assertions": len(g),
                "needs_review": needs_review,
                "region": regions[0] if regions else "",
                "source": _excel_safe(" | ".join(source_bits)[:2000]),
                "quote": _excel_safe(" | ".join(quote_bits)[:4000]),
                "notes": _excel_safe(" | ".join(dict.fromkeys(notes_bits))[:1000]),
                "entity_a_polygon_source": ha.polygon_source,
                "entity_a_polygon_id": ha.polygon_id,
                "entity_a_display_name": ha.display_name,
                "entity_a_match_method": ha.match_method,
                "entity_a_resolve_source": ha.resolve_source,
                "entity_b_polygon_source": hb.polygon_source,
                "entity_b_polygon_id": hb.polygon_id,
                "entity_b_display_name": hb.display_name,
                "entity_b_match_method": hb.match_method,
                "entity_b_resolve_source": hb.resolve_source,
                "homeland_complete": complete,
                "pair_key": pk,
            }
        )
    return pd.DataFrame(rows)


def _load_previous_fills(
    path: Path = RA_WORKPACK_XLSX,
    sheet: str = RA_UNMATCHED_SHEET,
) -> dict[str, dict[str, str]]:
    """Preserve in-progress unmatched edits across rebuilds (from RA_workpack)."""
    if not path.is_file():
        return {}
    try:
        prev = pd.read_excel(path, sheet_name=sheet)
    except ValueError:
        return {}
    out: dict[str, dict[str, str]] = {}
    for _, r in prev.iterrows():
        ent = _clean(r.get("entity"))
        if not ent:
            continue
        fills = {c: _clean(r.get(c)) for c in UNMATCHED_FILL_COLS}
        # Accept custom column name `source` as resolve_source
        if not fills.get("resolve_source"):
            fills["resolve_source"] = _clean(r.get("source"))
        if any(fills.values()):
            out[ent.casefold()] = fills
    return out


_REGION_DISPLAY = {
    "east africa": "East Africa",
    "eastern africa": "East Africa",
    "easternafrica": "East Africa",
    "west africa": "West Africa",
    "western africa": "West Africa",
    "westernafrica": "West Africa",
    "central africa": "Central Africa",
    "centralafrica": "Central Africa",
    "north africa": "North Africa",
    "northern africa": "North Africa",
    "northernafrica": "North Africa",
    "south africa": "Southern Africa",
    "southern africa": "Southern Africa",
    "southernafrica": "Southern Africa",
    "burkinafaso": "West Africa",
    "burkina faso": "West Africa",
}


def _norm_region(val: str) -> str:
    raw = _clean(val)
    if not raw:
        return ""
    return _REGION_DISPLAY.get(raw.casefold().replace("_", " ").replace("-", " "), raw)


def build_unmatched(
    pairs: pd.DataFrame,
    assertions: pd.DataFrame | None = None,
) -> pd.DataFrame:
    previous = _load_previous_fills()
    missing: dict[str, dict] = {}
    for _, r in pairs.iterrows():
        for side in ("a", "b"):
            src = _clean(r.get(f"entity_{side}_polygon_source"))
            name = _clean(r.get(f"entity_{side}"))
            if not name or src in VALID_HOMELAND:
                continue
            key = name.casefold()
            if key not in missing:
                fills = previous.get(key, {})
                missing[key] = {
                    "entity": name,
                    "region": set(),
                    "polygon_source": fills.get("polygon_source", ""),
                    "polygon_id": fills.get("polygon_id", ""),
                    "display_name": fills.get("display_name", ""),
                    "resolve_source": fills.get("resolve_source", ""),
                    "coder": fills.get("coder", ""),
                    "aliases": fills.get("aliases", ""),
                    "notes": fills.get("notes", ""),
                    "example_pair_partner": _clean(r.get(f"entity_{'b' if side == 'a' else 'a'}")),
                    "n_pairs": 0,
                    "source_flags_seen": set(),
                }
            missing[key]["n_pairs"] += 1
            reg = _norm_region(_clean(r.get("region")))
            if reg:
                missing[key]["region"].add(reg)
            for flag in _clean(r.get("source_flags")).split(";"):
                if flag:
                    missing[key]["source_flags_seen"].add(flag)

    if assertions is not None and not assertions.empty:
        for _, ar in assertions.iterrows():
            reg = _norm_region(_clean(ar.get("region")))
            if not reg:
                continue
            for col in ("entity_a", "entity_b"):
                key = _clean(ar.get(col)).casefold()
                if key in missing:
                    missing[key]["region"].add(reg)

    rows = []
    for m in missing.values():
        rows.append(
            {
                "entity": m["entity"],
                "region": "; ".join(sorted(m["region"])),
                "polygon_source": m["polygon_source"],
                "polygon_id": m["polygon_id"],
                "display_name": m["display_name"],
                "resolve_source": m["resolve_source"],
                "coder": m["coder"],
                "aliases": m["aliases"],
                "notes": m["notes"],
                "example_pair_partner": m["example_pair_partner"],
                "n_pairs": m["n_pairs"],
                "source_flags_seen": ";".join(sorted(m["source_flags_seen"])),
            }
        )
    cols = [
        "entity",
        "region",
        "polygon_source",
        "polygon_id",
        "display_name",
        "resolve_source",
        "coder",
        "aliases",
        "notes",
        "example_pair_partner",
        "n_pairs",
        "source_flags_seen",
    ]
    if not rows:
        return pd.DataFrame(columns=cols)
    return pd.DataFrame(rows)[cols].sort_values(["n_pairs", "entity"], ascending=[False, True])


def run_build() -> None:
    ensure_output_dirs()
    print("Loading sources…")
    assertions = load_all_cross_assertions()
    print(
        f"  assertions={len(assertions)}  by source:\n"
        + assertions["source_dataset"].value_counts().to_string().replace("\n", "\n    ")
    )
    assertions.to_csv(ASSERTIONS_CSV, index=False)
    print(f"  → {ASSERTIONS_CSV}")

    print("Resolving homelands + building pair table…")
    pairs = build_pair_table(assertions)
    complete_n = int(pairs["homeland_complete"].sum()) if len(pairs) else 0
    print(f"  unique pairs={len(pairs)}  homeland_complete={complete_n}")

    unmatched = build_unmatched(pairs, assertions)
    kept, removed, added = sync_icmid_unmatched_sheet(unmatched)
    if ICMID_MANUAL_XLSX.is_file():
        print(
            f"  synced ICMID {ICMID_UNMATCHED_SHEET!r}: "
            f"{kept} rows (removed {removed} resolved, +{added} new)"
        )

    pairs_out = pairs.drop(columns=["pair_key"], errors="ignore")
    with pd.ExcelWriter(CROSS_GROUP_XLSX, engine="openpyxl") as writer:
        pairs_out.to_excel(writer, sheet_name="cross_group", index=False)
    print(f"  → {CROSS_GROUP_XLSX}")
    # Drop stale CSV twin if present (xlsx is the single pair deliverable).
    if CROSS_GROUP_CSV.is_file():
        CROSS_GROUP_CSV.unlink()
        print(f"  removed duplicate {CROSS_GROUP_CSV.name}")

    print(
        f"  unmatched entities={len(unmatched)} "
        f"(fill via RA_workpack.xlsx / {RA_UNMATCHED_SHEET}; "
        "regen with export_ra_workpack.py)"
    )
    print("Done.")


def _run_map_pipeline() -> None:
    """Sync map inputs + build interactive HTML under output/jr_database/."""
    print("Building map deliverable (output/jr_database/)…")
    sync = _CODE / "visualization" / "sync_from_jr_database.py"
    build = _CODE / "visualization" / "build_cross_group_map.py"
    subprocess.check_call(
        [sys.executable, "-B", str(sync)],
        cwd=str(_PIPELINE),
    )
    subprocess.check_call(
        [sys.executable, "-B", str(build)],
        cwd=str(_PIPELINE),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Build consolidated cross-group JR database")
    parser.add_argument(
        "--apply-unmatched",
        action="store_true",
        help="Write filled RA_workpack 1_unmatched_entities into ethnic_entity_index (+ sync registry), then rebuild",
    )
    parser.add_argument(
        "--with-map",
        dest="with_map",
        action="store_true",
        default=True,
        help="Also sync + build the interactive map under output/jr_database/ (default: on)",
    )
    parser.add_argument(
        "--no-map",
        dest="with_map",
        action="store_false",
        help="Skip map build",
    )
    args = parser.parse_args()
    if args.apply_unmatched:
        apply_unmatched()
        get_resolver.cache_clear()
    run_build()
    if args.with_map:
        _run_map_pipeline()


if __name__ == "__main__":
    main()
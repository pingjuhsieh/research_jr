#!/usr/bin/env python3
"""Build consolidated cross-group JR database with homeland mapping.

Workflow (manual homeland fixes):
  1. Run build → output/jr_database/unmatched_entities.xlsx
  2. Fill polygon_source, polygon_id, resolve_source (and optional aliases)
  3. uv run python -B code/jr_database/build_cross_group.py --apply-unmatched

You normally only edit unmatched_entities.xlsx. That writes into
ethnic_entity_index.xlsx (the cumulative manual store). polygon_group_registry
is auto-synced — you do not need to maintain it for JR resolve.

Usage (from ICMID PingJu project root):
    uv run python -B code/jr_database/build_cross_group.py
    uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
"""
from __future__ import annotations

import argparse
import re
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
    MATCHED_LOG_XLSX,
    POLYGON_GROUP_REGISTRY_XLSX,
    UNMATCHED_XLSX,
    ensure_output_dirs,
)
from jr_database.resolve_homeland import VALID_HOMELAND, get_resolver  # noqa: E402
from jr_database.sources import load_all_cross_assertions  # noqa: E402

# Columns the reviewer fills in unmatched_entities.xlsx
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
            "notes": notes or "filled via unmatched_entities",
        }
    )
    return pd.concat([index, pd.DataFrame([row])], ignore_index=True)


def _append_matched_log(rows: list[dict]) -> None:
    """Permanent archive of applied unmatched fills (never wiped by rebuild)."""
    if not rows:
        return
    new = pd.DataFrame(rows)
    new["applied_at"] = pd.Timestamp.now().isoformat(timespec="seconds")
    if MATCHED_LOG_XLSX.is_file():
        old = pd.read_excel(MATCHED_LOG_XLSX)
        out = pd.concat([old, new], ignore_index=True)
    else:
        out = new
    # de-dupe on entity + polygon_id + resolve_source, keep latest
    out["_k"] = (
        out.get("entity", pd.Series(dtype=str)).fillna("").astype(str).str.casefold()
        + "|"
        + out.get("polygon_id", pd.Series(dtype=str)).fillna("").astype(str).str.upper()
        + "|"
        + out.get("resolve_source", pd.Series(dtype=str)).fillna("").astype(str)
    )
    out = out.drop_duplicates(subset=["_k"], keep="last").drop(columns=["_k"])
    MATCHED_LOG_XLSX.parent.mkdir(parents=True, exist_ok=True)
    out.to_excel(MATCHED_LOG_XLSX, index=False, sheet_name="matched")


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


def apply_unmatched(path: Path = UNMATCHED_XLSX) -> int:
    """Write filled unmatched rows into ethnic_entity_index.xlsx and sync registry."""
    if not path.is_file():
        raise FileNotFoundError(f"No unmatched file: {path}")
    um = pd.read_excel(path)
    if um.empty:
        print("unmatched file empty — nothing to apply")
        return 0

    index = load_index() if ETHNIC_ENTITY_INDEX_XLSX.is_file() else pd.DataFrame(columns=INDEX_COLUMNS)
    applied = 0
    alias_n = 0
    log_rows: list[dict] = []

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
        log_rows.append(
            {
                "entity": raw,
                "polygon_source": src,
                "polygon_id": pid,
                "display_name": display,
                "resolve_source": resolve_source,
                "coder": coder,
                "aliases": _clean(r.get("aliases")),
                "notes": notes,
                "example_pair_partner": _clean(r.get("example_pair_partner")),
                "n_pairs": r.get("n_pairs", ""),
                "source_flags_seen": _clean(r.get("source_flags_seen")),
            }
        )

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
    _append_matched_log(log_rows)
    reg_added = sync_registry_from_index(index)
    print(f"Applied {applied} entity fills (+{alias_n} aliases) → {ETHNIC_ENTITY_INDEX_XLSX}")
    print(f"Matched log → {MATCHED_LOG_XLSX}  (+{len(log_rows)} this run)")
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


def _load_previous_fills(path: Path) -> dict[str, dict[str, str]]:
    """Preserve in-progress unmatched edits across rebuilds."""
    if not path.is_file():
        return {}
    prev = pd.read_excel(path)
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


def build_unmatched(pairs: pd.DataFrame) -> pd.DataFrame:
    previous = _load_previous_fills(UNMATCHED_XLSX)
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
            for flag in _clean(r.get("source_flags")).split(";"):
                if flag:
                    missing[key]["source_flags_seen"].add(flag)

    rows = []
    for m in missing.values():
        rows.append(
            {
                "entity": m["entity"],
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

    unmatched = build_unmatched(pairs)
    print(f"  unmatched entities={len(unmatched)}")

    pairs_out = pairs.drop(columns=["pair_key"], errors="ignore")
    pairs_out.to_csv(CROSS_GROUP_CSV, index=False)
    with pd.ExcelWriter(CROSS_GROUP_XLSX, engine="openpyxl") as writer:
        pairs_out.to_excel(writer, sheet_name="cross_group", index=False)
    print(f"  → {CROSS_GROUP_XLSX}")
    print(f"  → {CROSS_GROUP_CSV}")

    unmatched.to_excel(UNMATCHED_XLSX, index=False, sheet_name="unmatched")
    print(f"  → {UNMATCHED_XLSX}")
    print("Done.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build consolidated cross-group JR database")
    parser.add_argument(
        "--apply-unmatched",
        action="store_true",
        help="Write filled unmatched_entities.xlsx into ethnic_entity_index (+ sync registry), then rebuild",
    )
    args = parser.parse_args()
    if args.apply_unmatched:
        apply_unmatched()
        get_resolver.cache_clear()
    run_build()


if __name__ == "__main__":
    main()

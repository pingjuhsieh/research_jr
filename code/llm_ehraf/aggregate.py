"""Aggregate per-assertion JR rows into review-table pairs.

Aggregate assertion rows into review-table pairs for export.
"""
from __future__ import annotations

import hashlib
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

_VIS_DIR = Path(__file__).resolve().parent.parent.parent / "code" / "visualization"
if str(_VIS_DIR) not in sys.path:
    sys.path.insert(0, str(_VIS_DIR))

from polygon_registry import canonicalize_entity_name, normalize_entity_for_pair  # noqa: E402

CSV_FIELDNAMES = [
    "relationship_id",
    "scope_coded",
    "region",
    "ethnography_group",
    "entity_a_canonical",
    "entity_b_canonical",
    "entity_a_type",
    "entity_b_type",
    "relation_type_coded",
    "symmetry_coded",
    "relation_labels",
    "local_terms",
    "supporting_quote_raw",
    "confidence_mean",
    "confidence_max",
    "n_assertions",
    "n_source_docs",
    "source_docs",
    "assertion_ids",
]


def _pair_key(a: str, b: str) -> tuple[str, str]:
    return tuple(sorted([normalize_entity_for_pair(a), normalize_entity_for_pair(b)]))


def _relationship_id(scope: str, a: str, b: str, region: str, ethno: str) -> str:
    raw = f"{scope}|{a}|{b}|{region}|{ethno}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


def _join_unique(values: list[str], sep: str = " | ") -> str:
    seen: set[str] = set()
    out: list[str] = []
    for v in values:
        s = (v or "").strip()
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return sep.join(out)


def aggregate_relationships(
    rows: list[dict[str, Any]],
    scope: str,
    *,
    between_pair_only: bool = False,
) -> list[dict[str, Any]]:
    """Collapse assertion rows that share the same unordered entity pair.

    ``between_pair_only`` drops rows where either entity is missing or equal.
    """
    buckets: dict[tuple[str, str, str, str], list[dict[str, Any]]] = defaultdict(list)

    for row in rows:
        if row.get("scope_coded") != scope:
            continue
        a_raw = canonicalize_entity_name(str(row.get("entity_a_raw") or ""))
        b_raw = canonicalize_entity_name(str(row.get("entity_b_raw") or ""))
        if between_pair_only and (not a_raw or not b_raw or a_raw == b_raw):
            continue
        if not a_raw and not b_raw:
            continue
        region = str(row.get("region") or "").strip()
        ethno = str(row.get("ethnography_group_name") or row.get("ethnography_group") or "").strip()
        key = (*_pair_key(a_raw or "?", b_raw or "?"), region, ethno)
        buckets[key].append({**row, "_a": a_raw, "_b": b_raw})

    out: list[dict[str, Any]] = []
    for (_ka, _kb, region, ethno), group in sorted(buckets.items(), key=lambda x: x[0]):
        # Prefer lexicographic canonical order for display
        a_display = group[0]["_a"]
        b_display = group[0]["_b"]
        if normalize_entity_for_pair(a_display) > normalize_entity_for_pair(b_display):
            a_display, b_display = b_display, a_display

        confs = [float(r.get("confidence") or 0.0) for r in group]
        docs = [str(r.get("doc_id") or "").strip() for r in group]
        docs = [d for d in docs if d]
        assertion_ids = [str(r.get("assertion_id") or "").strip() for r in group]
        assertion_ids = [a for a in assertion_ids if a]

        # Orient types / labels with a_display
        a_type = b_type = ""
        for r in group:
            if canonicalize_entity_name(str(r.get("entity_a_raw") or "")) == a_display:
                a_type = str(r.get("entity_a_type") or "")
                b_type = str(r.get("entity_b_type") or "")
                break
            if canonicalize_entity_name(str(r.get("entity_b_raw") or "")) == a_display:
                a_type = str(r.get("entity_b_type") or "")
                b_type = str(r.get("entity_a_type") or "")
                break

        rel_types = [str(r.get("relation_type_coded") or "").strip() for r in group]
        symmetries = [str(r.get("symmetry_coded") or "").strip() for r in group]
        labels = [str(r.get("relation_label_raw") or "").strip() for r in group]
        terms = [str(r.get("local_term_raw") or "").strip() for r in group]
        quotes = [str(r.get("supporting_quote_raw") or r.get("quote_text") or "").strip() for r in group]

        unique_syms = {s for s in symmetries if s}
        if len(unique_syms) > 1:
            symmetry = "mixed"
        elif unique_syms:
            symmetry = next(iter(unique_syms))
        else:
            symmetry = ""

        out.append(
            {
                "relationship_id": _relationship_id(scope, a_display, b_display, region, ethno),
                "scope_coded": scope,
                "region": region,
                "ethnography_group": ethno,
                "entity_a_canonical": a_display,
                "entity_b_canonical": b_display,
                "entity_a_type": a_type,
                "entity_b_type": b_type,
                "relation_type_coded": _join_unique(rel_types, sep=";"),
                "symmetry_coded": symmetry,
                "relation_labels": _join_unique(labels),
                "local_terms": _join_unique(terms),
                "supporting_quote_raw": _join_unique(quotes),
                "confidence_mean": round(sum(confs) / len(confs), 4) if confs else 0.0,
                "confidence_max": max(confs) if confs else 0.0,
                "n_assertions": len(group),
                "n_source_docs": len(set(docs)),
                "source_docs": ";".join(sorted(set(docs))),
                "assertion_ids": ";".join(assertion_ids),
            }
        )
    return out

"""Document metadata helpers (doc_id, region, ethnography group)."""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Tuple

KNOWN_REGIONS = [
    "CentralAfrica", "EasternAfrica", "SouthernAfrica",
    "WesternAfrica", "NorthernAfrica", "MiddleAfrica",
    "SoutheastAsia", "SouthAsia", "EastAsia", "Oceania",
    "NorthAmerica", "SouthAmerica", "CentralAmerica",
    "Europe", "MiddleEast",
]

ETHNIC_GROUP_TO_REGION = {
    "akan": "WesternAfrica",
    "bambara": "WesternAfrica",
    "dogon": "WesternAfrica",
    "fon": "WesternAfrica",
    "fulani": "WesternAfrica",
    "hausa": "WesternAfrica",
    "igbo": "WesternAfrica",
    "kanuri": "WesternAfrica",
    "katab": "WesternAfrica",
    "kpelle": "WesternAfrica",
    "mende": "WesternAfrica",
    "mossi": "WesternAfrica",
    "nupe": "WesternAfrica",
    "tallensi": "WesternAfrica",
    "tiv": "WesternAfrica",
    "wolof": "WesternAfrica",
    "yoruba": "WesternAfrica",
}

FOLDER_REGION_ALIASES = {
    "wester africa": "WesternAfrica",
    "western africa": "WesternAfrica",
    "resource wester africa": "WesternAfrica",
    "resource western africa": "WesternAfrica",
}


def doc_id_from_pdf(pdf_path: Path) -> str:
    return f"/{pdf_path.stem.replace(' ', '_')}"


def ethnography_group_from_doc_id(doc_id: str) -> str:
    base = doc_id.strip("/")
    return base.split("_")[0].strip() if "_" in base else base.strip()


def markdown_path_for_doc(paths, doc_id: str, *, cleaned: bool = True) -> Path:
    stem = doc_id.strip("/").replace("/", "_")
    root = paths.markdown_clean if cleaned else paths.markdown_raw
    return root / f"{stem}.md"


def _normalize_path_part(part: str) -> str:
    p = part.strip()
    p = re.sub(r"^resource\s+", "", p, flags=re.I).strip()
    p = re.sub(r"-\d{8}T\d+Z.*$", "", p)
    p = re.sub(r"\s*\(\d+\)\s*$", "", p).strip()
    return FOLDER_REGION_ALIASES.get(p.lower(), p)


def detect_region(pdf_path: Path, root: Path) -> str:
    try:
        rel = pdf_path.relative_to(root)
    except ValueError:
        return "UNKNOWN"

    parts = rel.parts[:-1]
    if not parts:
        return "UNKNOWN"

    normalized = [_normalize_path_part(p) for p in parts]

    for part in normalized:
        alias = FOLDER_REGION_ALIASES.get(part.lower())
        if alias:
            return alias
        for region in KNOWN_REGIONS:
            if region.lower() == part.lower():
                return region
            if part.lower().startswith(region.lower()):
                return region

    for part in normalized:
        region = ETHNIC_GROUP_TO_REGION.get(part.lower())
        if region:
            return region

    first = normalized[0]
    if first in KNOWN_REGIONS:
        return first
    return first if first else "UNKNOWN"


def collect_pdfs(root: Path) -> List[Tuple[Path, str]]:
    if not root.is_dir():
        return []

    seen: set[Path] = set()
    results: List[Tuple[Path, str]] = []
    for pattern in ("*.pdf", "*.PDF"):
        for pdf_path in root.rglob(pattern):
            resolved = pdf_path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            results.append((pdf_path, detect_region(pdf_path, root)))

    results.sort(key=lambda item: str(item[0]).lower())
    return results


def list_pdfs(pdf_root: Path) -> List[Tuple[Path, str]]:
    return collect_pdfs(pdf_root)

"""eHRAF markdown cleanup helpers (footer, OCM sidebar, page chrome)."""
from __future__ import annotations

import re
import sqlite3
from functools import lru_cache
from pathlib import Path
from typing import List, Set, Tuple

_PIPELINE_ROOT = Path(__file__).resolve().parent.parent.parent
_LEGACY_OCM_DB = Path()  # optional legacy corpus; unused after archive cleanup

_ARTIFACT_PATTERNS: List[Tuple[re.Pattern[str], str]] = [
    (re.compile(r"insert_drive_file\d+"), " "),
    (re.compile(r"\f"), "\n"),  # form-feed page breaks from PDF export
    (re.compile(r"\bclick\s+here\b", re.I), " "),
    (re.compile(r"\breturn\s+to\s+search\b", re.I), " "),
    (re.compile(r"\bdownload\s+pdf\b", re.I), " "),
    (re.compile(r"\bview\s+full\s+record\b", re.I), " "),
    (re.compile(r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M\s*$", re.M), ""),
    (re.compile(
        r"^\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}\s*[AP]M\s+.+eHRAF World Cultures\s*$",
        re.M | re.I,
    ), ""),
    (re.compile(r"https://ehrafworldcultures\.yale\.edu\S*", re.I), " "),
]

_SKIP_LINE_TEXTS = frozenset({
    "return to search",
    "back to results",
    "next page",
    "previous page",
    "general inquiries:",
    "issues and bugs:",
    "·",
    "return to search",
})

_SKIP_LINE_PATS = [
    re.compile(r"^\s*\d{1,3}\s+Prospect Street\s*$", re.I),
    re.compile(r"^\s*New Haven,?\s*CT\s+06511\s*$", re.I),
    re.compile(r"^\s*hraf@yale\.edu\s*$", re.I),
    re.compile(r"^\s*hraf-support@yale\.edu\s*$", re.I),
    re.compile(r"^\s*Human Relations Area Files\s*$", re.I),
    re.compile(r"^\s*eHRAF World Cultures\s*$", re.I),
    re.compile(r"Terms and Conditions", re.I),
    re.compile(r"^\s*Accessibility\s*$", re.I),
    re.compile(r"Cookie Policy", re.I),
    re.compile(r"^\s*\|"),
    re.compile(r"^\s*[-·|]+\s*$"),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^[\uE000-\uF8FF\u200B-\u200D\ufeff\uE000-\uF8FF]+$"),
    re.compile(r"^\s*\s*$"),
]

_FOOTER_LINE_PAT = re.compile(
    r"\bHuman Relations Area Files\b"
    r"|\bhraf-support@yale\.edu\b"
    r"|\bhraf@yale\.edu\b"
    r"|\beHRAF World Cultures\b"
    r"|\bProspect Street\b"
    r"|\bTerms and Conditions\b",
    re.I,
)

_FOOTER_ANCHOR = re.compile(
    r"(?:^|\n)\s*Human Relations Area Files\b"
    r"|(?:^|\n)\s*(?:\d{1,3}\s+)?Prospect Street\b"
    r"|(?:^|\n)\s*General Inquiries\s*:"
    r"|(?:^|\n)\s*Issues and Bugs\s*:"
    r"|(?:^|\n)\s*https://ehrafworldcultures\.yale\.edu",
    re.I | re.M,
)

_OCM_CODE_LINE = re.compile(r"^\s*\d{3,4}\s*$")
_INLINE_OCM = re.compile(r"(?<!\d)\b\d{3}\b(?!\d)")

_METADATA_LINE_PAT = re.compile(
    r"^(author\(s\):|document type:|culture \(owc\):|original page:|"
    r"region:|field date:|coverage date:|place coverage:|"
    r"section title\(s\):|sub region:)",
    re.I,
)

# eHRAF per-page metadata block (title line after date header)
_EHRAF_TITLE_LINE = re.compile(
    r"^.+\s+-\s+eHRAF World Cultures\s*$",
    re.I,
)


@lru_cache(maxsize=1)
def _ocm_sidebar_labels() -> Set[str]:
    """OCM topic labels from legacy corpus vocabulary (lowercased for match)."""
    labels: Set[str] = set()
    if _LEGACY_OCM_DB.is_file():
        try:
            con = sqlite3.connect(_LEGACY_OCM_DB)
            rows = con.execute(
                "SELECT DISTINCT label FROM ocm_code WHERE label IS NOT NULL AND length(label) BETWEEN 3 AND 80"
            ).fetchall()
            con.close()
            for (label,) in rows:
                clean = (label or "").strip()
                if clean and not clean[0].isdigit() and "unknown" not in clean.lower():
                    labels.add(clean.lower())
        except sqlite3.Error:
            pass
    # Frequent sidebar fragments seen in markitdown exports
    labels.update({
        "localized kin groups",
        "kin relationships",
        "ingroup antagonisms",
        "cultural participation",
        "external relations",
        "regulation of marriage",
        "adolescent activities",
        "community structure",
        "ethos",
        "intra-community conflict",
    })
    return labels


def _is_ocm_sidebar_line(stripped: str) -> bool:
    if _OCM_CODE_LINE.match(stripped):
        return True
    return stripped.lower() in _ocm_sidebar_labels()


def _normalize_whitespace(text: str) -> str:
    text = text.replace("\u00a0", " ")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_trailing_footer_block(text: str) -> str:
    m = _FOOTER_ANCHOR.search(text)
    if m:
        text = text[: m.start()]
    return text


def _should_skip_line(stripped: str) -> bool:
    if not stripped:
        return False
    low = stripped.lower()
    if low in _SKIP_LINE_TEXTS:
        return True
    for pat in _SKIP_LINE_PATS:
        if pat.search(stripped):
            return True
    if _FOOTER_LINE_PAT.search(stripped):
        return True
    if _EHRAF_TITLE_LINE.match(stripped):
        return True
    if _is_ocm_sidebar_line(stripped):
        return True
    return False


def clean_markdown(text: str) -> str:
    """Remove eHRAF UI noise, OCM sidebars, Yale footer, and page chrome."""
    text = text or ""
    for pat, rep in _ARTIFACT_PATTERNS:
        text = pat.sub(rep, text)

    text = _strip_trailing_footer_block(text)

    kept_lines: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            kept_lines.append("")
            continue
        if _should_skip_line(stripped):
            continue
        if _METADATA_LINE_PAT.match(stripped):
            continue
        kept_lines.append(line)

    text = "\n".join(kept_lines)
    text = _INLINE_OCM.sub(" ", text)
    return _normalize_whitespace(text)


def truncate_for_llm(text: str, max_chars: int) -> tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    head = max_chars // 2
    tail = max_chars - head - 80
    marker = "\n\n[... document truncated for model context ...]\n\n"
    return text[:head] + marker + text[-tail:], True

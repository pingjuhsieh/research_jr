"""Load/save flat JR pair tables under output/jr_database/."""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

from config import CROSS_GROUP_MAP_XLSX, WITHIN_GROUP_XLSX

_ILLEGAL_XLSX_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _excel_safe_frame(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for c in out.columns:
        if out[c].dtype == object or str(out[c].dtype) == "string":
            out[c] = out[c].map(
                lambda v: _ILLEGAL_XLSX_RE.sub("", v) if isinstance(v, str) else v
            )
    return out


def load_within_group(path: Path | None = None) -> pd.DataFrame:
    p = path or WITHIN_GROUP_XLSX
    if not p.is_file():
        # One-time fallback if an old CSV is still present
        legacy = p.with_suffix(".csv")
        if legacy.is_file():
            df = pd.read_csv(legacy)
        else:
            raise FileNotFoundError(p)
    elif p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
    else:
        df = pd.read_excel(p)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def save_within_group(df: pd.DataFrame, path: Path | None = None) -> Path:
    p = path or WITHIN_GROUP_XLSX
    p.parent.mkdir(parents=True, exist_ok=True)
    _excel_safe_frame(df).to_excel(p, index=False, sheet_name="within_group")
    return p


def load_cross_group_map(path: Path | None = None) -> pd.DataFrame:
    p = path or CROSS_GROUP_MAP_XLSX
    if not p.is_file():
        legacy = p.parent / "between_group_joking.xlsx"
        if legacy.is_file():
            p = legacy
        else:
            raise FileNotFoundError(path or CROSS_GROUP_MAP_XLSX)
    return pd.read_excel(p)


def save_cross_group_map(df: pd.DataFrame, path: Path | None = None) -> Path:
    p = path or CROSS_GROUP_MAP_XLSX
    p.parent.mkdir(parents=True, exist_ok=True)
    _excel_safe_frame(df).to_excel(p, index=False, sheet_name="cross_group")
    return p

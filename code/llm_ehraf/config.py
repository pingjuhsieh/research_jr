"""Paths and LLM settings for the llm_ehraf pipeline."""
from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parent.parent.parent  # code/llm_ehraf → project root
load_dotenv(PIPELINE_ROOT / ".env")

DATA_ROOT = Path(os.getenv("ICMID_DATA_ROOT", PIPELINE_ROOT / "data")).expanduser().resolve()
OUTPUT_ROOT = Path(os.getenv("ICMID_OUTPUT_ROOT", PIPELINE_ROOT / "output")).expanduser().resolve()

MODEL_EXTRACT = os.getenv("OPENAI_MODEL_EXTRACT_V2", os.getenv("OPENAI_MODEL_EXTRACT", "gpt-4.1-mini-2025-04-14"))
EXTRACT_MAX_TOKENS = int(os.getenv("EXTRACT_MAX_TOKENS_V2", os.getenv("EXTRACT_MAX_TOKENS", "16000")))
MAX_DOC_CHARS = int(os.getenv("MAX_DOC_CHARS_V2", "120000"))
MAX_LLM_RETRIES = int(os.getenv("MAX_LLM_RETRIES", "5"))
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0"))
LLM_SEED = int(os.getenv("LLM_SEED", "42"))


@dataclass(frozen=True)
class DocPipelinePaths:
    project_root: Path
    data_root: Path
    output_root: Path
    ethnography_pages: Path
    markdown_raw: Path
    markdown_clean: Path
    jr_sqlite: Path
    logs: Path
    export_dir: Path
    all_relationships_csv: Path
    within_groups_csv: Path
    between_groups_csv: Path


@lru_cache(maxsize=1)
def get_paths() -> DocPipelinePaths:
    base = OUTPUT_ROOT / "llm_ehraf"
    export_dir = base / "export"
    return DocPipelinePaths(
        project_root=PIPELINE_ROOT,
        data_root=DATA_ROOT,
        output_root=OUTPUT_ROOT,
        ethnography_pages=DATA_ROOT / "ethnography_pages",
        markdown_raw=base / "markdown_raw",
        markdown_clean=base / "markdown_clean",
        jr_sqlite=base / "ehraf_jr_doc.sqlite",
        logs=base / "logs",
        export_dir=export_dir,
        all_relationships_csv=export_dir / "llm_ehraf_joking_relationships.csv",
        within_groups_csv=export_dir / "llm_ehraf_within_kin.csv",
        between_groups_csv=export_dir / "llm_ehraf_cross_group.csv",
    )


def ensure_dirs() -> DocPipelinePaths:
    paths = get_paths()
    for directory in (
        paths.markdown_raw,
        paths.markdown_clean,
        paths.logs,
        paths.export_dir,
        paths.ethnography_pages,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return paths

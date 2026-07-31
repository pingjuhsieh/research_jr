"""Paths for the consolidated JR database builder."""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

PIPELINE_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PIPELINE_ROOT / ".env")

DATA_ROOT = Path(os.getenv("ICMID_DATA_ROOT", PIPELINE_ROOT / "data")).expanduser().resolve()
OUTPUT_ROOT = Path(os.getenv("ICMID_OUTPUT_ROOT", PIPELINE_ROOT / "output")).expanduser().resolve()

SOURCES_ROOT = DATA_ROOT / "sources"
LOOKUP_ROOT = DATA_ROOT / "lookup"
GIS_ROOT = DATA_ROOT / "gis"

# Raw / curated inputs (data/)
KEERTHANA_CROSS_XLSX = SOURCES_ROOT / "keerthana_cross_group.xlsx"
ICMID_MANUAL_XLSX = SOURCES_ROOT / "icmid_manual_africa.xlsx"
ETHNIC_ENTITY_INDEX_XLSX = LOOKUP_ROOT / "ethnic_entity_index.xlsx"
POLYGON_GROUP_REGISTRY_XLSX = LOOKUP_ROOT / "polygon_group_registry.xlsx"

MURDOCK_SHP = GIS_ROOT / "murdock" / "Murdock_Map_2020.shp"
GREG_SHP = GIS_ROOT / "greg" / "GREG.shp"
GEOEPR_SHP = GIS_ROOT / "geoepr" / "GeoEPR-2021.shp"

# LLM eHRAF intermediate export
LLM_EHRAF_JR_CSV = OUTPUT_ROOT / "llm_ehraf" / "export" / "llm_ehraf_joking_relationships.csv"

# Intermediate + final outputs
JR_DB_OUTPUT = OUTPUT_ROOT / "jr_database"
RESULT_OUTPUT = OUTPUT_ROOT / "result"

ASSERTIONS_CSV = JR_DB_OUTPUT / "merge_cross_assertions.csv"
UNMATCHED_XLSX = JR_DB_OUTPUT / "unmatched_entities.xlsx"
MATCHED_LOG_XLSX = JR_DB_OUTPUT / "matched_entities_log.xlsx"
CROSS_GROUP_XLSX = RESULT_OUTPUT / "cross_group.xlsx"
CROSS_GROUP_CSV = RESULT_OUTPUT / "cross_group.csv"


def ensure_output_dirs() -> None:
    JR_DB_OUTPUT.mkdir(parents=True, exist_ok=True)
    RESULT_OUTPUT.mkdir(parents=True, exist_ok=True)

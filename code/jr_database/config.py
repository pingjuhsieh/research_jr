"""Paths for the consolidated JR database builder.

All deliverables (tables + map) live flat under ``output/jr_database/``.
"""
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

# Inputs
KEERTHANA_CROSS_XLSX = SOURCES_ROOT / "keerthana_cross_group.xlsx"
ICMID_MANUAL_XLSX = SOURCES_ROOT / "ICMID- Africa.xlsx"
ETHNIC_ENTITY_INDEX_XLSX = LOOKUP_ROOT / "ethnic_entity_index.xlsx"
POLYGON_GROUP_REGISTRY_XLSX = LOOKUP_ROOT / "polygon_group_registry.xlsx"

MURDOCK_SHP = GIS_ROOT / "murdock" / "Murdock_Map_2020.shp"
GREG_SHP = GIS_ROOT / "greg" / "GREG.shp"
GEOEPR_SHP = GIS_ROOT / "geoepr" / "GeoEPR-2021.shp"

LLM_EHRAF_JR_CSV = OUTPUT_ROOT / "llm_ehraf" / "export" / "llm_ehraf_joking_relationships.csv"
LLM_EHRAF_CROSS_CSV = OUTPUT_ROOT / "llm_ehraf" / "export" / "llm_ehraf_cross_group.csv"

# Outputs — everything flat under jr_database/
JR_DB_OUTPUT = OUTPUT_ROOT / "jr_database"
RESULT_OUTPUT = JR_DB_OUTPUT  # alias

ASSERTIONS_CSV = JR_DB_OUTPUT / "merge_cross_assertions.csv"
RA_WORKPACK_XLSX = JR_DB_OUTPUT / "RA_workpack.xlsx"
RA_UNMATCHED_SHEET = "1_unmatched_entities"
CROSS_GROUP_XLSX = JR_DB_OUTPUT / "cross_group.xlsx"
CROSS_GROUP_CSV = JR_DB_OUTPUT / "cross_group.csv"
SHEET2_JR_PAIRS_XLSX = JR_DB_OUTPUT / "sheet2_jr_pairs.xlsx"

# Map (same folder)
CROSS_GROUP_MAP_HTML = JR_DB_OUTPUT / "jr_map.html"
JR_MAP_HTML = CROSS_GROUP_MAP_HTML  # alias: map covers cross + within + kin
JR_RECORDS_JSON = JR_DB_OUTPUT / "jr_records.json"
# Map reshape of cross_group (+ assertion-level cols); regen by sync_from_jr_database
CROSS_GROUP_MAP_XLSX = JR_DB_OUTPUT / "cross_group_map.xlsx"
WITHIN_GROUP_XLSX = JR_DB_OUTPUT / "within_group.xlsx"
GROUP_INTENSITY_CSV = JR_DB_OUTPUT / "group_intensity_summary.csv"
UNRESOLVED_CSV = JR_DB_OUTPUT / "unresolved_entities.csv"
UNMAPPED_REGISTRY_CSV = JR_DB_OUTPUT / "unmapped_polygon_registry.csv"


def ensure_output_dirs() -> None:
    JR_DB_OUTPUT.mkdir(parents=True, exist_ok=True)

"""Local paths for the ICMID visualization pipeline (Ping-Ju)."""
from __future__ import annotations

from pathlib import Path

VIS_ROOT = Path(__file__).resolve().parent
PIPELINE_ROOT = VIS_ROOT.parent.parent  # code/visualization → project root

# Keerthana originals — used only for one-time --import-keerthana bootstrap
# Prefer local copy under data/sources/; fall back to sibling Keerthana folder.
KEERTHANA_ROOT = PIPELINE_ROOT.parents[1] / "ICMID Keerthana" / "HRAF copy"
KEERTHANA_JOKING_XLSX = KEERTHANA_ROOT / "final_HRAF_joking.xlsx"

# ── Shared data (project-wide) ────────────────────────────────────────────────
DATA_ROOT = PIPELINE_ROOT / "data"
SOURCES_ROOT = DATA_ROOT / "sources"
LOOKUP_ROOT = DATA_ROOT / "lookup"
REFERENCE_ROOT = DATA_ROOT / "reference"
EA_ROOT = DATA_ROOT / "ea"

# ── GIS layers ────────────────────────────────────────────────────────────────
GIS_ROOT = DATA_ROOT / "gis"
MURDOCK_SHP = GIS_ROOT / "murdock" / "Murdock_Map_2020.shp"
GREG_SHP = GIS_ROOT / "greg" / "GREG.shp"
GEOEPR_SHP = GIS_ROOT / "geoepr" / "GeoEPR-2021.shp"

# ── JR coding sources (raw inputs) ────────────────────────────────────────────
BETWEEN_GROUP_SOURCE_XLSX = SOURCES_ROOT / "keerthana_cross_group.xlsx"
KEERTHANA_ETHNICS_XLSX = SOURCES_ROOT / "keerthana_ethnics.xlsx"
LEGACY_ETHNICS_XLSX = KEERTHANA_ETHNICS_XLSX

# ── Editable matching tables (lookup/) ────────────────────────────────────────
ETHNIC_ENTITY_INDEX_XLSX = LOOKUP_ROOT / "ethnic_entity_index.xlsx"
POLYGON_GROUP_REGISTRY_XLSX = LOOKUP_ROOT / "polygon_group_registry.xlsx"

# ── External reference lists ──────────────────────────────────────────────────
MURDOCK_EA_XLSX = EA_ROOT / "murdock_ea_concordance.xlsx"
JOSHUA_CSV = REFERENCE_ROOT / "joshua_project_peoples.csv"
THP_CSV = REFERENCE_ROOT / "thp_per_murdock.csv"

# ── LLM eHRAF export ──────────────────────────────────────────────────────────
DOC_LEVEL_JR_CSV = PIPELINE_ROOT / "output" / "llm_ehraf" / "export" / "llm_ehraf_joking_relationships.csv"

# ── Outputs (visualization pipeline) ──────────────────────────────────────────
OUTPUT_DIR = PIPELINE_ROOT / "output" / "visualization"
BETWEEN_GROUP_SOURCE_MERGED_XLSX = OUTPUT_DIR / "between_group_source_merged.xlsx"
BETWEEN_GROUP_JOKING_XLSX = OUTPUT_DIR / "between_group_joking.xlsx"
WITHIN_GROUPS_CSV = OUTPUT_DIR / "within_group.csv"
WITHIN_GROUPS_MERGED_CSV = WITHIN_GROUPS_CSV
JR_RECORDS_JSON = OUTPUT_DIR / "jr_records.json"
JR_SUMMARY_XLSX = OUTPUT_DIR / "ethnic_group_jr_summary.xlsx"
GROUP_INTENSITY_CSV = OUTPUT_DIR / "group_intensity_summary.csv"
UNMATCHED_HOMELANDS_XLSX = OUTPUT_DIR / "unmatched_homelands.xlsx"
CROSS_GROUP_MAP_HTML = OUTPUT_DIR / "cross_group_jr_map.html"
UNRESOLVED_CSV = OUTPUT_DIR / "unresolved_entities.csv"
UNMAPPED_REGISTRY_CSV = OUTPUT_DIR / "unmapped_polygon_registry.csv"

AFRICA_BBOX = (-25, -40, 55, 38)

# min_lat, min_lon, max_lat, max_lon — reject GIS placements outside Africa
AFRICA_BOUNDS = (-40.0, -25.0, 38.0, 55.0)


def in_africa_bounds(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    min_lat, min_lon, max_lat, max_lon = AFRICA_BOUNDS
    return min_lat <= lat <= max_lat and min_lon <= lon <= max_lon

REGION_COLORS = {
    "WesternAfrica": "#E07B39",
    "EasternAfrica": "#4C9BE8",
    "CentralAfrica": "#9B59B6",
    "NorthernAfrica": "#27AE60",
    "SouthernAfrica": "#E74C3C",
}
DEFAULT_REGION_COLOR = "#888888"

INTENSITY_COLORS: dict[int, str] = {
    0: "#f7f7f7",   # no JR
    1: "#fee5d9",   # kin only
    2: "#fcae91",   # within-group cross-lineage
    3: "#fb6a4a",   # cross-group only
    4: "#de2d26",   # 2 types
    5: "#a50f15",   # all 3 types
}

# Map non-standard region/country values found in Keerthana's data → canonical region
REGION_ALIAS: dict[str, str] = {
    # Countries in West Africa
    "burkinafaso": "WesternAfrica",
    "burkina faso": "WesternAfrica",
    "mali": "WesternAfrica",
    "niger": "WesternAfrica",
    "senegal": "WesternAfrica",
    "guinea": "WesternAfrica",
    "ghana": "WesternAfrica",
    "nigeria": "WesternAfrica",
    "togo": "WesternAfrica",
    "benin": "WesternAfrica",
    "ivory coast": "WesternAfrica",
    "cote d'ivoire": "WesternAfrica",
    "gambia": "WesternAfrica",
    "sierra leone": "WesternAfrica",
    "liberia": "WesternAfrica",
    "mauritania": "WesternAfrica",
    # Countries in East Africa
    "kenya": "EasternAfrica",
    "tanzania": "EasternAfrica",
    "uganda": "EasternAfrica",
    "ethiopia": "EasternAfrica",
    "somalia": "EasternAfrica",
    "rwanda": "EasternAfrica",
    "burundi": "EasternAfrica",
    "sudan": "NorthernAfrica",
    "south sudan": "EasternAfrica",
    # Countries in Central Africa
    "drc": "CentralAfrica",
    "congo": "CentralAfrica",
    "cameroon": "CentralAfrica",
    "central african republic": "CentralAfrica",
    "chad": "CentralAfrica",
    # Countries in North Africa
    "egypt": "NorthernAfrica",
    "morocco": "NorthernAfrica",
    "algeria": "NorthernAfrica",
    "tunisia": "NorthernAfrica",
    "libya": "NorthernAfrica",
    # Countries in Southern Africa
    "zambia": "SouthernAfrica",
    "zimbabwe": "SouthernAfrica",
    "mozambique": "SouthernAfrica",
    "south africa": "SouthernAfrica",
    "botswana": "SouthernAfrica",
    "namibia": "SouthernAfrica",
    "angola": "SouthernAfrica",
    # Data source tags (not regions) → use WesternAfrica as default since
    # most HRAF African data skews West/Central Africa
    "new_ehraf": "WesternAfrica",
    "hraf": "WesternAfrica",
    "ehraf": "WesternAfrica",
}

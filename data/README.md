# Shared data (`data/`) — raw / curated inputs only

Generated products live under `output/` (especially `output/jr_database/`).
Do not treat merge/map intermediates as source data.

## Layout

```
data/
├── ethnography_pages/          # Raw eHRAF PDFs
├── gis/                        # Murdock / GREG / GeoEPR shapefiles
├── ea/                         # Ethnographic Atlas + Africa grid constructs
│   └── murdock_ea_concordance.xlsx
├── external/EMG_NN_THPCCC/     # Third-party replication
├── sources/                    # Original JR coding workbooks
│   ├── keerthana_cross_group.xlsx
│   ├── keerthana_ethnics.xlsx
│   └── ICMID- Africa.xlsx
├── lookup/                     # Editable entity ↔ polygon matching only
│   ├── ethnic_entity_index.xlsx      # cumulative manual homeland store (+ resolve_source)
│   ├── polygon_group_registry.xlsx   # auto-synced for maps; usually ignore
│   ├── jr_polygon_aliases.csv
│   └── greg_no_murdock_worklist.xlsx
└── reference/                  # External name / attribute lists
    ├── joshua_project_peoples.csv
    └── thp_per_murdock.csv
```

Map intermediates (`cross_group_map.xlsx`, `jr_records.json`,
`group_intensity_summary.csv`, …) live in `output/jr_database/`.
Prefer `output/jr_database/cross_group.xlsx` for the consolidated JR database.

## Override

`ICMID_DATA_ROOT` in `.env` for an external data root (same layout).

# Visualization — joking relationship maps

```bash
bash code/visualization/scripts/run_map.sh
```

Open `output/visualization/cross_group_jr_map.html`.

This syncs from the consolidated JR database (`output/result/cross_group.csv` +
`output/jr_database/merge_cross_assertions.csv`), then rebuilds the map.

First-time Keerthana bootstrap (legacy, usually not needed):

```bash
uv run python code/visualization/prepare.py data --import-keerthana
```

## Pipeline

```
jr_database build → result/cross_group + merge_cross_assertions
        │
sync_from_jr_database.py → between_group_joking.xlsx + jr_records.json
        │
build_cross_group_map.py
        │
output/visualization/cross_group_jr_map.html
```

Shared data: `data/sources/`, `data/lookup/`, `data/gis/`, `data/reference/`.
Map outputs: `output/visualization/`.

## Manual commands

```bash
uv run python -B code/visualization/sync_from_jr_database.py
uv run python -B code/visualization/build_cross_group_map.py
```

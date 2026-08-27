# jr_database — consolidated joking-relationship database

Merge JR sources → homeland resolve → pair table + optional map.
Map **code** lives in `code/visualization/`; map **files** land in `output/jr_database/`.

See **`output/jr_database/README.md`** for why that folder has many files and which
ones are canonical vs regenerable.

## What you run

```bash
bash code/jr_database/scripts/run.sh              # pairs + map
bash code/jr_database/scripts/run.sh --no-map
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
uv run python -B code/jr_database/export_ra_workpack.py
uv run python -B code/jr_database/export_sheet2_jr_pairs.py   # updates ICMID JR_pair sheet
```

## Layout (`code/jr_database/`)

| File | Role |
|------|------|
| `build_cross_group.py` | Main build (+ map by default) |
| `sources.py` | Load Keerthana / LLM / ICMID assertions |
| `resolve_homeland.py` | Entity → Murdock / GREG / GeoEPR |
| `export_ra_workpack.py` | Single RA workbook |
| `export_sheet2_jr_pairs.py` | Expand Sheet2 → ICMID `JR_pair` sheet |
| `config.py` | Paths |
| `lib/` | Internal helpers for RA workpack (do not run directly) |

## Homeland workflow

Edit only **`RA_workpack.xlsx` → `1_unmatched_entities`**
(`polygon_source`, `polygon_id`, optional `resolve_source` / `aliases`), then:

```bash
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
uv run python -B code/jr_database/export_ra_workpack.py
```

Resolve order: `ethnic_entity_index` → registry aliases → GIS exact name.

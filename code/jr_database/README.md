# jr_database — consolidated joking-relationship database

Merge all JR sources, focus first on **cross-group**, map entities to
Murdock / GREG / GeoEPR homelands.

## Homeland workflow (only one place to edit)

```
build → unmatched_entities.xlsx  (fill these columns)
              │
              ▼  --apply-unmatched
     ethnic_entity_index.xlsx    ← cumulative manual store
              │
              ▼  auto-sync
     polygon_group_registry.xlsx ← you usually ignore this
```

**You normally only edit** `output/jr_database/unmatched_entities.xlsx`:

| Column | Fill with |
|--------|-----------|
| `polygon_source` | `murdock` \| `greg` \| `geopr` |
| `polygon_id` | ID / name in that layer |
| `display_name` | optional nicer label |
| `resolve_source` | **where you got the match** (wiki URL, paper, …). Column name `source` also accepted. |
| `coder` | who filled it (optional) |
| `aliases` | optional other spellings → same polygon (comma-separated) |
| `notes` | optional |

Applied rows are archived forever in `output/jr_database/matched_entities_log.xlsx`
(and also stored on `ethnic_entity_index.xlsx` / result `entity_*_resolve_source`).

Then:

```bash
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
```

Partial fills are preserved if you rebuild without applying.
Do **not** fill polygon for non-groups (e.g. “little boys”) — leave blank or fix the JR source instead.

`ethnic_entity_index.xlsx` is the long-term store (Keerthana bootstrap + all applied fills).
`polygon_group_registry.xlsx` is kept for the map pipeline and auto-synced; prefer putting
aliases in the unmatched `aliases` column (they become index rows).

## Inputs (`data/`)

| File | Source |
|------|--------|
| `data/sources/keerthana_cross_group.xlsx` | Keerthana (`analysis` / `og`) |
| `data/sources/icmid_manual_africa.xlsx` | Manual coding: Sheet2 Murdock × F-column partners; Sheet1 confirmed; Sheet3 ignored |
| `data/lookup/ethnic_entity_index.xlsx` | Manual entity → polygon (+ `resolve_source`) |
| `data/gis/` | Murdock / GREG / GeoEPR |

LLM export: `output/llm_ehraf/export/llm_ehraf_joking_relationships.csv`

## Resolve order

1. `ethnic_entity_index` (manual, carries `resolve_source`)
2. `polygon_group_registry` aliases (legacy / map)
3. GIS exact name (murdock → greg → geopr); `resolve_source` = `gis:…`

## Outputs

| Path | Role |
|------|------|
| `output/jr_database/merge_cross_assertions.csv` | Every raw assertion + provenance |
| `output/jr_database/unmatched_entities.xlsx` | **Work queue** for manual polygon fill |
| **`output/result/cross_group.xlsx`** | Clean pair table + homeland + resolve_source columns |
| `output/result/cross_group.csv` | Same as main sheet |

## Commands

```bash
uv run python -B code/jr_database/build_cross_group.py
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
```

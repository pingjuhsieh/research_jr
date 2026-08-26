# jr_database — consolidated joking-relationship database

Merge all JR sources, focus first on **cross-group**, map entities to
Murdock / GREG / GeoEPR homelands.

## Homeland workflow (only one place to edit)

```
export_ra_workpack → RA_workpack.xlsx  (fill sheet 1_unmatched_entities)
              │
              ▼  --apply-unmatched
     ethnic_entity_index.xlsx    ← cumulative manual store
              │
              ▼  auto-sync
     polygon_group_registry.xlsx ← you usually ignore this
```

**You normally only edit** `output/jr_database/RA_workpack.xlsx` sheet `1_unmatched_entities`:

| Column | Fill with |
|--------|-----------|
| `region` | auto — East / West / Central / North / Southern Africa (do not fill) |
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
uv run python -B code/jr_database/export_ra_workpack.py
```

Partial fills are preserved if you rebuild without applying (read back from the workpack sheet).
Do **not** fill polygon for non-groups (e.g. “little boys”) — leave blank or fix the JR source instead.

`ethnic_entity_index.xlsx` is the long-term store (Keerthana bootstrap + all applied fills).
`polygon_group_registry.xlsx` is kept for the map pipeline and auto-synced; prefer putting
aliases in the unmatched `aliases` column (they become index rows).

## Inputs (`data/`)

| File | Source |
|------|--------|
| `data/sources/keerthana_cross_group.xlsx` | Keerthana (`analysis` only; `og` dropped as llm_ehraf duplicate) |
| `data/sources/ICMID- Africa.xlsx` | Manual coding: Sheet2 Murdock × F-column partners; Sheet1 confirmed; Sheet3 ignored |
| `data/lookup/ethnic_entity_index.xlsx` | Manual entity → polygon (+ `resolve_source`) |
| `data/gis/` | Murdock / GREG / GeoEPR |

LLM export: `output/llm_ehraf/export/llm_ehraf_joking_relationships.csv`
(only `scope_coded=cross_group` is kept; kinship / within_group ignored)

## Resolve order

1. `ethnic_entity_index` (manual, carries `resolve_source`)
2. `polygon_group_registry` aliases (legacy / map)
3. GIS exact name (murdock → greg → geopr); `resolve_source` = `gis:…`

## Outputs

| Path | Role |
|------|------|
| `output/jr_database/merge_cross_assertions.csv` | Every raw assertion + provenance |
| **`output/jr_database/RA_workpack.xlsx`** | **Only RA work queue** (resolve + one-sided + Sheet2/3 import; see `0_STEPS`) |
| **`output/result/cross_group.xlsx`** | Clean pair table + homeland + resolve_source columns |
| `output/result/cross_group.csv` | Same as main sheet |

## Commands

```bash
uv run python -B code/jr_database/build_cross_group.py
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
uv run python -B code/jr_database/export_ra_workpack.py
```

`export_ra_workpack.py` writes **`output/jr_database/RA_workpack.xlsx`** only.

## Sheet2 → one-row-per-JR pairs

```bash
uv run python -B code/jr_database/export_sheet2_jr_pairs.py
```

Adds / refreshes sheet **`JR_pair`** on `data/sources/ICMID- Africa.xlsx`
(Sheet2 unchanged):

- One undirected pair per resolved homeland pair (aliases like Kugni/KUNYI collapse)
- Prefer the side whose `Source_Quote` mentions the partner **or its aliases**
- If neither matches: prefer `Other sources`, flag `source_review`
- Rows with `Auditor` filled are preserved (exact name-duplicates dropped only)

Also writes `output/result/sheet2_jr_pairs.xlsx`.
# ICMID PingJu — pipeline

## Layers

| Layer | Contents |
|-------|----------|
| `data/` | Raw inputs only |
| `code/llm_ehraf/` | eHRAF → LLM JR extraction |
| `code/jr_database/` | Consolidate sources + homeland map |
| `output/llm_ehraf/` | LLM intermediates |
| `output/jr_database/` | Merge intermediates + `RA_workpack.xlsx` |
| `output/result/` | **Final clean files** |

## A. LLM eHRAF

```bash
uv run python -B code/llm_ehraf/run.py convert
uv run python -B code/llm_ehraf/run.py extract --force
uv run python -B code/llm_ehraf/run.py export
```

Writes `output/llm_ehraf/export/llm_ehraf_joking_relationships.csv` (and cross / within_kin splits).

## B. Consolidated cross-group JR database

Sources:

1. LLM eHRAF (`scope=cross_group`)
2. Keerthana `data/sources/keerthana_cross_group.xlsx` (`analysis` only)
3. ICMID manual `data/sources/ICMID- Africa.xlsx`
   (Sheet2 main: Murdock row × column F comma-separated JR partners; Sheet1 confirmed; Sheet3 ignored)

```bash
uv run python -B code/jr_database/build_cross_group.py
```

- Assertions (full provenance): `output/jr_database/merge_cross_assertions.csv`
- **RA work queue:** `output/jr_database/RA_workpack.xlsx` (regen with `export_ra_workpack.py`)
- **Result:** `output/result/cross_group.xlsx`

Fill `polygon_source`, `polygon_id`, and `resolve_source` (wiki URL etc.) on
`RA_workpack.xlsx` sheet `1_unmatched_entities` — optionally `aliases` — then:

```bash
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
uv run python -B code/jr_database/export_ra_workpack.py
```

## C. Map (optional)

```bash
bash code/visualization/scripts/run_map.sh
```

Syncs from `output/result/cross_group` + assertions, then writes
`output/visualization/cross_group_jr_map.html`.

## D. Settlement / climate (downstream)

| Module | Scripts | Outputs |
|--------|---------|---------|
| Settlement | `code/settlement/` | `output/settlement/` (+ EA constructs in `data/ea/`) |
| Climate | `code/climate/` | `output/climate/{panels,tables,figures}/` |

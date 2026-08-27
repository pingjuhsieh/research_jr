# ICMID PingJu — pipeline

## Layers

| Layer | Contents |
|-------|----------|
| `data/` | Raw inputs only |
| `code/llm_ehraf/` | eHRAF → LLM JR extraction |
| `code/jr_database/` | Consolidate sources + homeland + map deliverables |
| `code/visualization/` | Map builder (writes into `output/jr_database/`) |
| `output/llm_ehraf/` | LLM intermediates |
| `output/jr_database/` | **All JR database products** (pairs, RA workpack, map) |

## A. LLM eHRAF

```bash
uv run python -B code/llm_ehraf/run.py convert
uv run python -B code/llm_ehraf/run.py extract --force
uv run python -B code/llm_ehraf/run.py export
```

Writes `output/llm_ehraf/export/llm_ehraf_joking_relationships.csv` (and cross / within_kin splits).

## B. Consolidated JR database (+ map)

Sources:

1. LLM eHRAF (`scope=cross_group`)
2. Keerthana `data/sources/keerthana_cross_group.xlsx` (`analysis` only)
3. ICMID manual `data/sources/ICMID- Africa.xlsx`
   (Sheet2 / `JR_pair`; Sheet1 confirmed; Sheet3 ignored)

```bash
# Full deliverable tree (pairs + assertions + map)
bash code/jr_database/scripts/run.sh

# Or Python directly (map on by default)
uv run python -B code/jr_database/build_cross_group.py
uv run python -B code/jr_database/build_cross_group.py --no-map
```

Writes under `output/jr_database/`:

| File | Role |
|------|------|
| `cross_group.xlsx` | Clean undirected pairs + homeland |
| `RA_workpack.xlsx` | RA queue (regen: `export_ra_workpack.py`) |
| `jr_map.html` | Interactive map (cross + within + kin) |
| `jr_records.json` | Detail-panel records (map intermediate) |

Fill `polygon_source`, `polygon_id`, and `resolve_source` on
`RA_workpack.xlsx` sheet `1_unmatched_entities`, then:

```bash
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
uv run python -B code/jr_database/export_ra_workpack.py
```

## C. Map only (optional)

```bash
bash code/visualization/scripts/run_map.sh
```

## D. Settlement / climate (downstream)

| Module | Scripts | Outputs |
|--------|---------|---------|
| Settlement | `code/settlement/` | `output/settlement/` (+ EA constructs in `data/ea/`) |
| Climate | `code/climate/` | `output/climate/{panels,tables,figures}/` |

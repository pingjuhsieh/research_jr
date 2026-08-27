# `output/jr_database/` — what lives here and why

This folder is the **single JR deliverable tree**. Three pipelines write here
on purpose (no separate `result/` / `visualization/` folders):

1. **Database build** (`build_cross_group.py`) — pair table + assertions
2. **RA tools** (`export_ra_workpack.py`, apply-unmatched) — work queue
3. **Map build** (`code/visualization/…`) — HTML + map-only intermediates

Map **code** stays in `code/visualization/`; only the files land here.

---

## Keep / open these (canonical)

| File | Role |
|------|------|
| `cross_group.xlsx` | **Cross-group** undirected pairs + homeland (analysis deliverable) |
| `within_group.xlsx` | **Within-group / kinship** pairs (separate scope; not in cross) |
| `merge_cross_assertions.csv` | One row per source assertion (full provenance) |
| `RA_workpack.xlsx` | RA queue (`0_STEPS`, unmatched, reciprocity, import) |
| `cross_group_jr_map.html` | Interactive map (open in a browser) |

Canonical ICMID pair coding is the **`JR_pair` sheet** on
`data/sources/ICMID- Africa.xlsx` — not a second copy in this folder.

---

## Map intermediates (regen; do not edit by hand)

| File | Why it exists |
|------|----------------|
| `cross_group_map.xlsx` | Map reshape of cross data (assertion-level rows + `homeland_key` for coloring). **Not** a second database — only the map builder needs this shape. Regenerated from `cross_group.xlsx` + `merge_cross_assertions.csv`. |
| `jr_records.json` | Detail-panel payloads for the HTML |
| `group_intensity_summary.csv` | Per-homeland intensity; also used by settlement scripts |

---

## Commands

```bash
bash code/jr_database/scripts/run.sh              # pairs + map
uv run python -B code/jr_database/export_ra_workpack.py
uv run python -B code/jr_database/build_cross_group.py --apply-unmatched
```

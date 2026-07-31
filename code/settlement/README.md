# Settlement — JR × Ethnographic Atlas / Africa grid

Numbered scripts under `code/settlement/`; run from **ICMID PingJu project root**.
Generated products go to `output/settlement/`. EA/grid constructs stay in `data/ea/`.

## Pipeline

```
data/lookup/jr_polygon_aliases.csv
output/visualization/group_intensity_summary.csv
        │
export_cross_group_homelands.py  →  output/settlement/cross_group_homeland_units.csv
00_generate_pure_grid.R          →  data/ea/grid_sf.rds
01_get_ea.do                     →  data/ea/* settlement constructs
02_overlay_jr_on_grid.R          →  data/ea/grid_cross_group_jr.dta
03_jr_descriptive_stat.do        →  output/settlement/*.csv|.dta
04_plot_jr_grid_maps.R           →  output/settlement/*.png
```

## Commands

```bash
uv run python -B code/settlement/export_cross_group_homelands.py
Rscript code/settlement/00_generate_pure_grid.R
# Stata: do code/settlement/01_get_ea.do
Rscript code/settlement/02_overlay_jr_on_grid.R
# Stata: do code/settlement/03_jr_descriptive_stat.do
Rscript code/settlement/04_plot_jr_grid_maps.R
```

# Climate — JR × climate / conflict

Scripts only under `code/climate/`. Generated panels, tables, and figures go to `output/climate/`.

## Layout

```
code/climate/
├── r/
└── stata/

output/climate/
├── panels/    # .dta panels / cell overlays
├── tables/    # estimates, crosswalk comparisons
└── figures/   # maps
```

## Eberle track

Requires `../Replication_Heat_and_Hate_ReStat_Data/`.

```bash
Rscript code/climate/r/01_overlay_jr_on_eberle_cells.R
# Stata from project root:
do code/climate/stata/00_master.do
```

## McGuirk–Nunn track

```bash
Rscript code/climate/r/01_build_mn_crosswalk.R
Rscript code/climate/r/02_extract_mn_panel.R
Rscript code/climate/r/03_plot_maps.R
```

## Inputs

| Path | Role |
|------|------|
| `output/settlement/cross_group_homeland_units.csv` | JR homeland units |
| `data/gis/` | Murdock / GREG / GeoEPR |
| `data/ea/grid_sf.rds` | Africa grid |
| `../Replication_Heat_and_Hate_ReStat_Data/source/final_cell_year.dta` | Eberle panel |

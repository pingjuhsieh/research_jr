# Link McGuirk-Nunn replication cells to our 0.5-degree grid (grid_id).
# Run once before Stata JR pipeline.
#
# Output: output/climate/panels/mn_cell_crosswalk.dta
#         output/climate/tables/mn_grid_comparison.csv

library(haven)
library(dplyr)

# Project root (portable): run via Rscript from anywhere, or setwd interactively first.
.icmid_root <- local({
  ca <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", ca[grep("^--file=", ca)])
  if (length(f) && nzchar(f[[1]])) {
    normalizePath(file.path(dirname(f[[1]]), "../../.."), mustWork = TRUE)
  } else {
    getwd()
  }
})
setwd(.icmid_root)

panel_dir <- "output/climate/panels"
out_dir   <- "output/climate/tables"
dir.create(panel_dir, recursive = TRUE, showWarnings = FALSE)
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

mn <- read_dta("data/EMG_NN_THPCCC_replication_folder/data/EMG_NN_THPCCC_replication_data.dta")
ours <- read_dta("data/ea/my_own_murdock_grid_settlement_with_altnames.dta")

mn_cells <- mn |>
  filter(year == 2000) |>
  distinct(cell, x, y, MAP_name) |>
  mutate(lon_r = round(x, 2), lat_r = round(y, 2))

ours_cells <- ours |>
  mutate(lon_r = round(longitude, 2), lat_r = round(latitude, 2)) |>
  select(grid_id, longitude, latitude, lon_r, lat_r)

crosswalk <- inner_join(mn_cells, ours_cells, by = c("lon_r", "lat_r"))

if (nrow(crosswalk) != n_distinct(crosswalk$cell)) stop("Duplicate MN cell.")
if (nrow(crosswalk) != n_distinct(crosswalk$grid_id)) stop("Duplicate grid_id.")

comparison <- tibble(
  metric = c("MN cells", "Our grid cells", "Matched 1:1",
             "MN only", "Our grid only"),
  n = c(
    nrow(mn_cells), nrow(ours_cells), nrow(crosswalk),
    length(setdiff(mn_cells$cell, crosswalk$cell)),
    length(setdiff(ours_cells$grid_id, crosswalk$grid_id))
  )
)

write.csv(comparison, file.path(out_dir, "mn_grid_comparison.csv"), row.names = FALSE)
write_dta(crosswalk, file.path(panel_dir, "mn_cell_crosswalk.dta"))

cat("Matched:", nrow(crosswalk), "->", file.path(panel_dir, "mn_cell_crosswalk.dta"), "\n")

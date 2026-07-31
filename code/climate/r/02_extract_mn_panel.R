# Extract MN cell-year panel (climate, conflict, FE ids) and map to grid_id.
# Optional: only needed if you want MN data separate from Eberle replication.
#
# Output: output/climate/panels/mn_cell_panel.dta
#         output/climate/panels/mn_cell_climate_means.dta

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
dir.create(panel_dir, recursive = TRUE, showWarnings = FALSE)

mn <- read_dta("data/EMG_NN_THPCCC_replication_folder/data/EMG_NN_THPCCC_replication_data.dta")
crosswalk <- read_dta(file.path(panel_dir, "mn_cell_crosswalk.dta"))

climate_vars <- c("prec_gpcc", "temp", "phytomass",
                  "g_prec_gpcc", "g_temp", "g_phytomass",
                  "n1_g_prec_gpcc", "n1_g_temp", "n1_g_phytomass")
conflict_vars <- c("ucdp_all_10", "ucdp_state_10", "ucdp_nonstate_10",
                   "acled_all_10", "acled_state_10", "acled_nonstate_10",
                   "ucdp2020_num")
fe_vars <- c("cell", "cy", "kg_y", "country", "ctry")

panel <- mn |>
  select(all_of(fe_vars), year, x, y, MAP_name,
         all_of(climate_vars), all_of(conflict_vars), ln_pop1990, bs_np, bs_ag) |>
  left_join(crosswalk |> select(cell, grid_id), by = "cell")

means <- panel |>
  filter(year >= 1989, year <= 2018) |>
  group_by(grid_id, cell) |>
  summarise(
    mean_temp = mean(temp, na.rm = TRUE),
    mean_prec_gpcc = mean(prec_gpcc, na.rm = TRUE),
  .groups = "drop"
  )

write_dta(panel, file.path(panel_dir, "mn_cell_panel.dta"))
write_dta(means, file.path(panel_dir, "mn_cell_climate_means.dta"))

cat("Panel rows:", nrow(panel), "| cells:", n_distinct(panel$cell), "\n")

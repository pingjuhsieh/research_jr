# Climate descriptive maps (ggplot/sf). Run after r/02_extract_mn_panel.R.
#
# Output: output/climate/figures/*.png

library(sf)
library(dplyr)
library(ggplot2)
library(haven)
library(viridis)

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

fig_dir   <- "output/climate/figures"
panel_dir <- "output/climate/panels"
dir.create(fig_dir, recursive = TRUE, showWarnings = FALSE)

grid_sf    <- readRDS("data/ea/grid_sf.rds")
st_crs(grid_sf) <- 4326
means      <- read_dta(file.path(panel_dir, "mn_cell_climate_means.dta"))
murdock_sf <- st_read("data/gis/murdock/Murdock_Map_2020.shp", quiet = TRUE) |>
  st_transform(4326)

plot_sf <- grid_sf |>
  left_join(means, by = "grid_id") |>
  mutate(in_mn = !is.na(cell))

land_ids <- unique(
  st_join(grid_sf, murdock_sf[, "NAME"], join = st_intersects, left = FALSE)$grid_id
)
plot_land <- plot_sf |> filter(grid_id %in% land_ids)

theme_map <- theme_void() +
  theme(
    panel.background = element_rect(fill = "white", color = NA),
    plot.background  = element_rect(fill = "white", color = NA),
    legend.position  = "bottom",
    plot.title       = element_text(hjust = 0.5, face = "bold", size = 14),
    plot.subtitle    = element_text(hjust = 0.5, size = 9)
  )

map_coverage <- ggplot() +
  geom_sf(data = plot_land |> filter(!in_mn), fill = "#e8e8e8", color = NA) +
  geom_sf(data = plot_land |> filter(in_mn),  fill = "#2166ac", color = NA) +
  theme_map +
  labs(title = "MN replication cells on 0.5-degree grid",
       subtitle = "Blue = MN sample; gray = grid only")

map_rain <- ggplot() +
  geom_sf(data = plot_land |> filter(is.na(mean_prec_gpcc)), fill = "#f7f7f7", color = NA) +
  geom_sf(data = plot_land |> filter(!is.na(mean_prec_gpcc)), aes(fill = mean_prec_gpcc), color = NA) +
  scale_fill_viridis_c(option = "C", name = "mm/day", na.value = "#f7f7f7") +
  theme_map +
  labs(title = "Mean rainfall (GPCC)", subtitle = "1989-2018 cell average")

map_temp <- ggplot() +
  geom_sf(data = plot_land |> filter(is.na(mean_temp)), fill = "#f7f7f7", color = NA) +
  geom_sf(data = plot_land |> filter(!is.na(mean_temp)), aes(fill = mean_temp), color = NA) +
  scale_fill_viridis_c(option = "A", direction = -1, name = "deg C", na.value = "#f7f7f7") +
  theme_map +
  labs(title = "Mean temperature (CRU)", subtitle = "1989-2018 cell average")

ggsave(file.path(fig_dir, "MN_Grid_Sample_Coverage_Map.png"), map_coverage, width = 9, height = 10, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "MN_Grid_Mean_Rainfall_Map.png"),      map_rain,     width = 9, height = 10, dpi = 300, bg = "white")
ggsave(file.path(fig_dir, "MN_Grid_Mean_Temperature_Map.png"),   map_temp,     width = 9, height = 10, dpi = 300, bg = "white")

cat("Wrote figures ->", fig_dir, "\n")

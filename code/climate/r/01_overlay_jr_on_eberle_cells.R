# Overlay cross-group JR homelands onto Eberle replication grid cells.
# Uses Eberle cell IDs directly — no grid_id crosswalk needed.
#
# Prerequisite: code/settlement/export_cross_group_homelands.py
#               Replication_Heat_and_Hate_ReStat_Data/source/final_cell_year.dta
#
# Output: output/climate/panels/eberle_cell_jr.dta  (one row per Eberle cell)

library(sf)
library(dplyr)
library(haven)

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

eberle_path <- "../Replication_Heat_and_Hate_ReStat_Data/source/final_cell_year.dta"
units_path  <- "output/settlement/cross_group_homeland_units.csv"
out_path    <- "output/climate/panels/eberle_cell_jr.dta"

dir.create(dirname(out_path), recursive = TRUE, showWarnings = FALSE)

if (!file.exists(units_path)) {
  stop("Run first: python code/settlement/export_cross_group_homelands.py")
}

# --- Eberle 0.5-degree cells (centroids from replication package) ------------
cells <- read_dta(eberle_path) |>
  filter(year == 2000) |>
  distinct(cell, lat, lon) |>
  filter(!is.na(lat), !is.na(lon))

half <- 0.25  # 0.5 x 0.5 degree cells centered on lat/lon
cell_polys <- lapply(seq_len(nrow(cells)), function(i) {
  lon <- cells$lon[i]
  lat <- cells$lat[i]
  ring <- matrix(c(
    lon - half, lat - half,
    lon + half, lat - half,
    lon + half, lat + half,
    lon - half, lat + half,
    lon - half, lat - half
  ), ncol = 2, byrow = TRUE)
  st_polygon(list(ring))
})
cells_sf <- st_sf(
  cell = cells$cell,
  lat  = cells$lat,
  lon  = cells$lon,
  geometry = st_sfc(cell_polys, crs = 4326)
)

# --- JR homeland polygons (same sources as code/settlement/step2) ------------------
units <- read.csv(units_path, stringsAsFactors = FALSE)
murdock_sf <- st_read("data/gis/murdock/Murdock_Map_2020.shp", quiet = TRUE) |>
  st_transform(4326)
greg_sf <- st_read("data/gis/greg/GREG.shp", quiet = TRUE) |>
  st_transform(4326)
geoepr_sf <- st_read("data/gis/geoepr/GeoEPR-2021.shp", quiet = TRUE) |>
  st_transform(4326)

pick_polygon <- function(source, name) {
  key <- toupper(trimws(name))
  hit <- NULL
  if (source == "murdock") {
    hit <- murdock_sf[toupper(murdock_sf$NAME) == key, ]
    if (nrow(hit) == 0) hit <- murdock_sf[grepl(key, toupper(murdock_sf$NAME), fixed = TRUE), ]
  } else if (source == "greg") {
    hit <- greg_sf[toupper(greg_sf$G1SHORTNAM) == key, ]
    if (nrow(hit) == 0) hit <- greg_sf[grepl(key, toupper(greg_sf$G1SHORTNAM), fixed = TRUE), ]
  } else if (source == "geopr") {
    hit <- geoepr_sf[toupper(geoepr_sf$group) == key, ]
    if (nrow(hit) == 0) hit <- geoepr_sf[grepl(key, toupper(geoepr_sf$group), fixed = TRUE), ]
  }
  if (is.null(hit) || nrow(hit) == 0) return(NULL)
  st_geometry(hit)
}

poly_units <- units[units$polygon_source %in% c("murdock", "greg", "geopr"), ]
jr_parts <- list()
for (i in seq_len(nrow(poly_units))) {
  geom <- pick_polygon(poly_units$polygon_source[i], poly_units$polygon_name[i])
  if (!is.null(geom) && length(geom) > 0) {
    jr_parts[[length(jr_parts) + 1]] <- st_sf(
      group_id = poly_units$group_id[i],
      geometry = geom
    )
  }
}
if (length(jr_parts) == 0) stop("No JR homeland polygons resolved.")
jr_homelands_sf <- bind_rows(jr_parts)

# Point-only homelands: assign to containing Eberle cell
point_units <- units[units$polygon_source == "point" & !is.na(units$lat) & units$lat != "", ]
point_cells <- integer(0)
if (nrow(point_units) > 0) {
  pts <- st_as_sf(
    data.frame(
      group_id = point_units$group_id,
      lon = as.numeric(point_units$lon),
      lat = as.numeric(point_units$lat)
    ),
    coords = c("lon", "lat"), crs = 4326
  )
  pt_join <- st_join(pts, cells_sf["cell"], join = st_within)
  point_cells <- unique(pt_join$cell)
}

# --- Spatial join: Eberle cell intersects JR homeland -------------------------
cell_join <- st_join(
  cells_sf,
  jr_homelands_sf["group_id"],
  join = st_intersects,
  left = TRUE
)

cell_jr <- cell_join |>
  st_drop_geometry() |>
  group_by(cell, lat, lon) |>
  summarise(
    n_jr_groups = n_distinct(group_id[!is.na(group_id)]),
    cross_group_jr = as.integer(any(!is.na(group_id))),
    .groups = "drop"
  )

if (length(point_cells) > 0) {
  cell_jr <- cell_jr |>
    mutate(cross_group_jr = pmax(cross_group_jr, as.integer(cell %in% point_cells)))
}

# Full cell list (JR = 0 where no overlap)
out <- cells |>
  left_join(cell_jr |> select(cell, cross_group_jr, n_jr_groups), by = "cell") |>
  mutate(
    cross_group_jr = ifelse(is.na(cross_group_jr), 0L, cross_group_jr),
    n_jr_groups = ifelse(is.na(n_jr_groups), 0L, n_jr_groups)
  )

stopifnot(nrow(out) == nrow(cells), !anyDuplicated(out$cell))

write_dta(out, out_path)

cat("Eberle cells:", nrow(out), "\n")
cat("Cells with cross-group JR:", sum(out$cross_group_jr == 1), "\n")
cat("Wrote ->", out_path, "\n")

# ==============================================================================
# Step 2: Overlay cross-group joking-relationship homelands onto 0.5° grid
# ==============================================================================
# Prerequisite: run export_cross_group_homelands.py first.
# Output: data/ea/grid_cross_group_jr.dta  (one row per grid_id)

library(sf)
library(dplyr)
library(haven)

# Project root (portable): run via Rscript from anywhere, or setwd interactively first.
.icmid_root <- local({
  ca <- commandArgs(trailingOnly = FALSE)
  f <- sub("^--file=", "", ca[grep("^--file=", ca)])
  if (length(f) && nzchar(f[[1]])) {
    normalizePath(file.path(dirname(f[[1]]), "../.."), mustWork = TRUE)
  } else {
    getwd()
  }
})
setwd(.icmid_root)

units_path <- "output/settlement/cross_group_homeland_units.csv"
grid_rds   <- "data/ea/grid_sf.rds"
out_dta    <- "data/ea/grid_cross_group_jr.dta"

if (!file.exists(units_path)) {
  stop("Run first: uv run python code/settlement/export_cross_group_homelands.py")
}

units <- read.csv(units_path, stringsAsFactors = FALSE)
grid_sf <- readRDS(grid_rds)
st_crs(grid_sf) <- 4326

# ── Load GIS layers ───────────────────────────────────────────────────────────
murdock_sf <- st_read("data/gis/murdock/Murdock_Map_2020.shp", quiet = TRUE) |>
  st_transform(4326)
greg_sf <- st_read("data/gis/greg/GREG.shp", quiet = TRUE) |>
  st_transform(4326)
geoepr_sf <- st_read("data/gis/geoepr/GeoEPR-2021.shp", quiet = TRUE) |>
  st_transform(4326)

pick_polygon <- function(source, name) {
  key <- toupper(trimws(name))
  if (source == "murdock") {
    hit <- murdock_sf[toupper(murdock_sf$NAME) == key, ]
    if (nrow(hit) == 0) hit <- murdock_sf[grepl(key, toupper(murdock_sf$NAME), fixed = TRUE), ]
  } else if (source == "greg") {
    hit <- greg_sf[toupper(greg_sf$G1SHORTNAM) == key, ]
    if (nrow(hit) == 0) hit <- greg_sf[grepl(key, toupper(greg_sf$G1SHORTNAM), fixed = TRUE), ]
  } else if (source == "geopr") {
    hit <- geoepr_sf[toupper(geoepr_sf$group) == key, ]
    if (nrow(hit) == 0) hit <- geoepr_sf[grepl(key, toupper(geoepr_sf$group), fixed = TRUE), ]
  } else {
    return(NULL)
  }
  if (nrow(hit) == 0) return(NULL)
  st_geometry(hit)
}

# ── Build combined JR homeland layer ─────────────────────────────────────────
poly_units <- units[units$polygon_source %in% c("murdock", "greg", "geopr"), ]
jr_parts <- list()

for (i in seq_len(nrow(poly_units))) {
  geom <- pick_polygon(poly_units$polygon_source[i], poly_units$polygon_name[i])
  if (!is.null(geom) && length(geom) > 0) {
    part <- st_sf(
      group_id = poly_units$group_id[i],
      geometry = geom
    )
    jr_parts[[length(jr_parts) + 1]] <- part
  } else {
    warning("No polygon for ", poly_units$group_id[i],
            " (", poly_units$polygon_source[i], ": ", poly_units$polygon_name[i], ")")
  }
}

if (length(jr_parts) == 0) stop("No JR homeland polygons resolved.")

jr_homelands_sf <- bind_rows(jr_parts)

# Point-only homelands (marker entities on the visualization map)
point_units <- units[units$polygon_source == "point" & !is.na(units$lat) & units$lat != "", ]
point_grid_ids <- integer(0)
if (nrow(point_units) > 0) {
  pts <- st_as_sf(
    data.frame(
      group_id = point_units$group_id,
      lon = as.numeric(point_units$lon),
      lat = as.numeric(point_units$lat)
    ),
    coords = c("lon", "lat"),
    crs = 4326
  )
  pt_join <- st_join(pts, grid_sf[, "grid_id"], join = st_within)
  point_grid_ids <- unique(pt_join$grid_id)
}

# ── Spatial join: grid cells intersecting any JR homeland ────────────────────
grid_join <- st_join(
  grid_sf[, "grid_id"],
  jr_homelands_sf[, "group_id"],
  join = st_intersects,
  left = TRUE
)

grid_jr <- grid_join |>
  st_drop_geometry() |>
  group_by(grid_id) |>
  summarise(
    n_jr_groups = n_distinct(group_id[!is.na(group_id)]),
    cross_group_jr = as.integer(any(!is.na(group_id))),
    .groups = "drop"
  )

# Add point-only cells
if (length(point_grid_ids) > 0) {
  grid_jr <- grid_jr |>
    mutate(cross_group_jr = pmax(cross_group_jr, as.integer(grid_id %in% point_grid_ids)))
}

# All grid cells (including those without JR)
all_grids <- grid_sf |>
  st_drop_geometry() |>
  select(grid_id) |>
  left_join(grid_jr, by = "grid_id") |>
  mutate(
    n_jr_groups = ifelse(is.na(n_jr_groups), 0L, n_jr_groups),
    cross_group_jr = ifelse(is.na(cross_group_jr), 0L, cross_group_jr)
  )

write_dta(all_grids, out_dta)

cat("JR homeland polygons used:", nrow(jr_homelands_sf), "\n")
cat("Point-only grid cells:", length(point_grid_ids), "\n")
cat("Grid cells with cross-group JR:", sum(all_grids$cross_group_jr == 1), "\n")
cat("Wrote →", out_dta, "\n")

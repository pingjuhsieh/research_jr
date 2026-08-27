# ==============================================================================
# Visualize joking-relationship (JR) patterns on the 0.5° Africa grid
# ==============================================================================
# Outputs (output/settlement/):
#   JR_Grid_Intensity_Map.png   — max JR intensity per cell (overlaps → highest)
#   JR_Grid_CrossGroup_Binary_Map.png — cross-group JR yes/no per cell
#
# Prerequisite: output/jr_database/group_intensity_summary.csv
#               (from Visualization pipeline / run_map.sh)

library(sf)
library(dplyr)
library(ggplot2)

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

out_dir <- "output/settlement"
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# ── Intensity palette (matches code/visualization/config.py) ─────────────────────
INTENSITY_COLORS <- c(
  "0" = "#f7f7f7",
  "1" = "#fee5d9",
  "2" = "#fcae91",
  "3" = "#fb6a4a",
  "4" = "#de2d26",
  "5" = "#a50f15"
)
INTENSITY_LABELS <- c(
  "0" = "No JR",
  "1" = "Within kin only",
  "2" = "Within-group (cross-lineage/caste)",
  "3" = "Cross-group only",
  "4" = "2 types of JR",
  "5" = "All 3 types of JR"
)
BINARY_COLORS <- c(
  "No cross-group JR"  = "#f0f0f0",
  "Cross-group JR"     = "#fb6a4a"
)

# ── Load data ─────────────────────────────────────────────────────────────────
grid_sf <- readRDS("data/ea/grid_sf.rds")
st_crs(grid_sf) <- 4326

intensity_df <- read.csv("output/jr_database/group_intensity_summary.csv", stringsAsFactors = FALSE)
intensity_df$group_id <- toupper(trimws(intensity_df$group))

aliases <- read.csv("data/lookup/jr_polygon_aliases.csv", stringsAsFactors = FALSE)
alias_map <- setNames(
  paste(aliases$polygon_source, aliases$polygon_name, sep = "|"),
  toupper(aliases$group_id)
)

murdock_sf <- st_read("data/gis/murdock/Murdock_Map_2020.shp", quiet = TRUE) |>
  st_transform(4326)
greg_sf <- st_read("data/gis/greg/GREG.shp", quiet = TRUE) |>
  st_transform(4326)
geoepr_sf <- st_read("data/gis/geoepr/GeoEPR-2021.shp", quiet = TRUE) |>
  st_transform(4326)

murdock_names <- toupper(murdock_sf$NAME)
greg_names    <- toupper(greg_sf$G1SHORTNAM)
geoepr_names  <- toupper(iconv(geoepr_sf$group, from = "UTF-8", to = "ASCII//TRANSLIT"))

resolve_source_name <- function(group_id) {
  if (group_id %in% names(alias_map)) {
    parts <- strsplit(alias_map[[group_id]], "|", fixed = TRUE)[[1]]
    return(list(source = parts[1], name = parts[2]))
  }
  if (group_id %in% murdock_names) {
    title <- murdock_sf$NAME[match(group_id, murdock_names)]
    return(list(source = "murdock", name = title))
  }
  if (group_id %in% greg_names) {
    title <- greg_sf$G1SHORTNAM[match(group_id, greg_names)]
    return(list(source = "greg", name = title))
  }
  if (group_id %in% geoepr_names) {
    idx <- match(group_id, geoepr_names)
    return(list(source = "geopr", name = geoepr_sf$group[idx]))
  }
  NULL
}

pick_polygon <- function(source, name) {
  key <- toupper(trimws(name))
  if (source == "murdock") {
    hit <- murdock_sf[toupper(murdock_sf$NAME) == key, ]
  } else if (source == "greg") {
    hit <- greg_sf[toupper(greg_sf$G1SHORTNAM) == key, ]
  } else if (source == "geopr") {
    hit <- geoepr_sf[toupper(iconv(geoepr_sf$group, from = "UTF-8", to = "ASCII//TRANSLIT")) == key, ]
  } else {
    return(NULL)
  }
  if (nrow(hit) == 0) return(NULL)
  st_geometry(hit)
}

# ── Build homeland polygons with intensity ────────────────────────────────────
jr_groups <- intensity_df[intensity_df$intensity > 0, ]
jr_parts <- list()
unmatched <- character(0)

for (i in seq_len(nrow(jr_groups))) {
  gid <- jr_groups$group_id[i]
  resolved <- resolve_source_name(gid)
  if (is.null(resolved)) {
    unmatched <- c(unmatched, gid)
    next
  }
  geom <- pick_polygon(resolved$source, resolved$name)
  if (is.null(geom) || length(geom) == 0) {
    unmatched <- c(unmatched, gid)
    next
  }
  jr_parts[[length(jr_parts) + 1]] <- st_sf(
    group_id = gid,
    intensity = jr_groups$intensity[i],
    n_iii = jr_groups$n_iii[i],
    geometry = geom
  )
}

if (length(unmatched) > 0) {
  message("Groups without GIS polygon (skipped): ", paste(unique(unmatched), collapse = ", "))
}

jr_homelands_sf <- bind_rows(jr_parts)

# ── Overlay onto grid: max intensity per cell ─────────────────────────────────
grid_int_join <- st_join(
  grid_sf[, "grid_id"],
  jr_homelands_sf[, c("group_id", "intensity", "n_iii")],
  join = st_intersects,
  left = TRUE
)

grid_attrs <- grid_int_join |>
  st_drop_geometry() |>
  group_by(grid_id) |>
  summarise(
    jr_intensity = if (all(is.na(intensity))) 0L else max(intensity, na.rm = TRUE),
    cross_group_jr = as.integer(any(n_iii > 0, na.rm = TRUE)),
    n_jr_groups = n_distinct(group_id[!is.na(group_id)]),
    .groups = "drop"
  )

plot_sf <- grid_sf |>
  left_join(grid_attrs, by = "grid_id") |>
  mutate(
    jr_intensity = ifelse(is.na(jr_intensity), 0L, jr_intensity),
    cross_group_jr = ifelse(is.na(cross_group_jr), 0L, cross_group_jr),
    intensity_factor = factor(
      jr_intensity,
      levels = 0:5,
      labels = unname(INTENSITY_LABELS[as.character(0:5)])
    ),
    cross_group_factor = factor(
      ifelse(cross_group_jr == 1, "Cross-group JR", "No cross-group JR"),
      levels = c("No cross-group JR", "Cross-group JR")
    )
  )

# Land cells: those intersecting the Murdock ethnic map (Africa coverage)
murdock_grid <- st_join(grid_sf, murdock_sf[, "NAME"], join = st_intersects, left = FALSE)
land_grid_ids <- unique(murdock_grid$grid_id)
plot_land <- plot_sf |> filter(grid_id %in% land_grid_ids)

theme_map <- theme_void() +
  theme(
    panel.background = element_rect(fill = "white", color = NA),
    plot.background = element_rect(fill = "white", color = NA),
    legend.position = "bottom",
    legend.title = element_text(face = "bold", size = 10),
    legend.text = element_text(size = 8),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 15),
    plot.subtitle = element_text(hjust = 0.5, size = 10),
    plot.margin = margin(8, 8, 8, 8)
  )

# ── Map 1: JR intensity (max when groups overlap) ─────────────────────────────
map_intensity <- ggplot() +
  geom_sf(
    data = plot_land,
    aes(fill = intensity_factor),
    color = NA
  ) +
  scale_fill_manual(
    values = setNames(INTENSITY_COLORS, unname(INTENSITY_LABELS[as.character(0:5)])),
    name = "JR intensity (max in cell)",
    drop = FALSE
  ) +
  theme_map +
  labs(
    title = "Joking Relationships on 0.5° Grid",
    subtitle = "Cell color = highest JR intensity among overlapping ethnic homelands"
  )

ggsave(
  file.path(out_dir, "JR_Grid_Intensity_Map.png"),
  plot = map_intensity,
  width = 9, height = 10, dpi = 300,
  bg = "white"
)

# ── Map 2: cross-group JR binary ──────────────────────────────────────────────
map_binary <- ggplot() +
  geom_sf(
    data = plot_land,
    aes(fill = cross_group_factor),
    color = NA
  ) +
  scale_fill_manual(values = BINARY_COLORS, name = "Cross-group JR") +
  theme_map +
  labs(
    title = "Joking Relationships on 0.5° Grid",
    subtitle = "Binary: cell intersects any homeland with cross-group JR (n_iii > 0)"
  )

ggsave(
  file.path(out_dir, "JR_Grid_CrossGroup_Binary_Map.png"),
  plot = map_binary,
  width = 9, height = 10, dpi = 300,
  bg = "white"
)

cat("Intensity map cells with JR > 0:", sum(plot_land$jr_intensity > 0), "\n")
cat("Binary map cells with cross-group JR:", sum(plot_land$cross_group_jr == 1), "\n")
cat("Wrote →", file.path(out_dir, "JR_Grid_Intensity_Map.png"), "\n")
cat("Wrote →", file.path(out_dir, "JR_Grid_CrossGroup_Binary_Map.png"), "\n")

print(map_intensity)
print(map_binary)

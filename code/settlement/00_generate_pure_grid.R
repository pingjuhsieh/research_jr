# Load required packages
# install.packages(c("sf", "dplyr", "haven", "ggplot2"))
library(sf)
library(dplyr)
library(haven)
library(ggplot2) # Added for plotting maps

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

# ==========================================
# 1. Create a 0.5-degree spatial grid for Africa
# ==========================================
print("Generating 0.5-degree spatial grid for Africa...")

# Define the approximate bounding box for Africa (Longitude: -20 to 55, Latitude: -35 to 40)
africa_bbox <- st_bbox(c(xmin = -20, ymin = -35, xmax = 55, ymax = 40), crs = st_crs(4326))

# Generate the 0.5 x 0.5 degree grid polygons
grid_geom <- st_make_grid(africa_bbox, cellsize = c(0.5, 0.5), square = TRUE)

# Convert to an sf (spatial features) object and assign a unique grid_id to each cell
grid_sf <- st_sf(grid_id = 1:length(grid_geom), geometry = grid_geom)

# Calculate the centroid coordinates for each grid cell (useful for future plotting or regressions)
centroids <- st_centroid(grid_geom)
coords <- st_coordinates(centroids)
grid_coords <- data.frame(grid_id = 1:length(grid_geom), 
                          longitude = coords[,1], 
                          latitude = coords[,2])

# Save the spatial grid object for future geographic operations
saveRDS(grid_sf, "./data/ea/grid_sf.rds")

# ==========================================
# 2. Read the Murdock map and perform spatial intersection
# ==========================================
print("Reading Murdock map and performing spatial join...")

# Load the 2020 version of the Murdock shapefile
murdock_sf <- st_read("./data/gis/murdock/Murdock_Map_2020.shp")

# Ensure the coordinate reference system (CRS) matches the grid (WGS84 / EPSG:4326)
murdock_sf <- st_transform(murdock_sf, 4326) 

# Perform spatial join: Assign Murdock ethnic names to intersecting grid cells.
# Note: If a grid cell intersects multiple polygons, it will generate multiple rows for that grid_id.
grid_murdock_joined <- st_join(grid_sf, murdock_sf, join = st_intersects)

# ==========================================
# 3. Clean up and export to Stata
# ==========================================
print("Cleaning data and exporting to Stata...")

grid_murdock_df <- grid_murdock_joined %>%
  st_drop_geometry() %>% # Remove heavy spatial geometry to create a clean tabular dataframe
  select(grid_id, NAME) %>%
  filter(!is.na(NAME)) %>% # Drop cells that fell in the ocean or empty areas (NAME is NA)
  distinct() # Remove duplicate rows just in case

# Merge the longitude and latitude back into the dataframe
final_export <- grid_murdock_df %>%
  left_join(grid_coords, by = "grid_id")

# Export as a Stata .dta file
write_dta(final_export, "./data/ea/pure_grid_to_murdock.dta")


# ==========================================
# 4. Plotting: Check which grid cells have data
# ==========================================

# Create a new column in grid_sf to indicate if a cell successfully matched with any ethnic group
grid_sf <- grid_sf %>%
  mutate(data_status = ifelse(grid_id %in% grid_murdock_df$grid_id, "Has Data (Land)", "No Data (Ocean/Empty)"))

# Plot the grid using ggplot2
coverage_plot <- ggplot() +
  geom_sf(data = grid_sf, aes(fill = data_status), color = NA) +
  scale_fill_manual(values = c("Has Data (Land)" = "#619CFF", "No Data (Ocean/Empty)" = "#F0F0F0")) +
  theme_void() +
  theme(legend.position = "bottom") +
  labs(fill = "Grid Status:")

# Display the plot in RStudio
print(coverage_plot)
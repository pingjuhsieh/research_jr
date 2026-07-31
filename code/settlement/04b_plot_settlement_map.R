# ==============================================================================
# R Script: Visualize Settlement Patterns with Diagnostic Categories
# ==============================================================================

library(sf)
library(dplyr)
library(haven)
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

# 1. Load the spatial grid and the newly generated Stata dataset
grid_sf <- readRDS("./data/ea/grid_sf.rds")
grid_data <- read_dta("./data/ea/my_own_murdock_grid_settlement_with_altnames.dta")

# 2. Join the data and convert settlement_type to a factor with 5 levels
plot_sf <- grid_sf %>%
  left_join(grid_data, by = "grid_id") %>%
  filter(!is.na(settlement_type)) %>%
  mutate(
    settlement_factor = factor(settlement_type, 
                               levels = c(1, 2, 3, 4, 5), 
                               labels = c("Settlers only", 
                                          "Nomads only", 
                                          "Mixed settlement",
                                          "Unmatched Ethnicity", 
                                          "Missing Settlement Data"))
  )


# 3. Generate the map
final_map <- ggplot() +
  geom_sf(data = plot_sf, 
          aes(fill = settlement_factor), 
          color = NA) +
  scale_fill_manual(values = c("Settlers only" = "#00BA38",         # Green
                               "Nomads only" = "#619CFF",           # Blue
                               "Mixed settlement" = "#F8766D",      # Red
                               "Unmatched Ethnicity" = "#808080",   # Dark Gray
                               "Missing Settlement Data" = "#D3D3D3"), # Light Gray
                    name = "Settlement Pattern") +
  theme_void() +
  theme(
    legend.position = "bottom",
    legend.title = element_text(face = "bold"),
    plot.title = element_text(hjust = 0.5, face = "bold", size = 16),
    plot.subtitle = element_text(hjust = 0.5, size = 12)
  ) +
  labs(
    title = "Settlement Patterns in Africa",
    subtitle = "Replicated using Murdock (1959) & Official 2024 Concordance"
  )

# 4. Display the map in RStudio
print(final_map)

# 5. Export the map to high-resolution PNG
ggsave("./output/settlement/Merge_Replicated_Settlement_Map.png", 
       plot = final_map, 
       width = 8, 
       height = 9, 
       dpi = 300)
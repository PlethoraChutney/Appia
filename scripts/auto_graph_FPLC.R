suppressMessages(library(tidyverse))
library(ggplot2)

# 1 Import ----------------------------------------------------------------

# These values are all determined by options given to the python script.
# Use the simpler manual_plot_traces.R script if you're changing these.
args = commandArgs(trailingOnly = TRUE)
no.ext <- str_sub(basename(args[1]), end = -5)
out.dir <- dirname(args[1])
min_frac <- as.integer(args[2])
max_frac <- as.integer(args[3])
low_ml <- as.integer(args[4])
high_ml <- as.integer(args[5])

data <- read_csv(args[1], col_types = 'dcddcci') %>%
  mutate(inst_frac = if_else(inst_frac < min_frac, 'Waste', if_else(inst_frac > max_frac, 'Waste', as.character(inst_frac))))

# 2 Plot ------------------------------------------------------------------

# * 2.1 Multi-experiment plots --------------------------------------------

if (length(levels(factor(data$Sample))) > 1) {
data %>%
  filter(Channel == 'mAU' & mL > low_ml & mL < high_ml) %>%
  group_by(Sample) %>%
  mutate(Normalized = ((Signal - min(Signal)) / (max(Signal) - min(Signal)))) %>%
  gather(key = Normalized, value = Signal, Signal, Normalized) %>%
  ungroup() %>%
  ggplot(aes(x = mL, y = Signal, color = Sample)) +
  facet_grid(Normalized ~ ., scales = 'free') +
  theme_light() +
  scale_color_viridis_d() +
  geom_line()
ggsave(filename = file.path(out.dir, paste('all_samples_', no.ext, '.pdf', sep = '')), width = 8, height = 5)
} else {
  data %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
    ggplot(aes(x = mL, y = Signal, color = Channel)) +
    theme_light() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    scale_color_viridis_d() +
    geom_line()
  ggsave(filename = file.path(out.dir, paste('all_channels_', no.ext, '.pdf', sep = '')), width = 6, height = 4)
}

# * 2.2 mAU fraction plots ------------------------------------------------

if (max_frac == 0) {
  data %>%
    filter(Channel == 'mAU') %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
    group_by(Sample) %>%
    ggplot() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    theme_light() +
    geom_line(aes(x = mL, y = Signal)) +
    facet_grid(Sample ~ ., scales = 'free')
  ggsave(filename = file.path(out.dir, paste('mAU_', no.ext, '.pdf', sep = '')), width = 6, height = 4)
}

if (max_frac > 0) {
  data %>%
    filter(Channel == 'mAU') %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
    group_by(Sample) %>%
    ggplot() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    theme_light() +
    scale_fill_viridis_d(limits = min_frac : max_frac) +
    labs(fill = 'Fraction') +
    geom_ribbon(aes(x = mL, ymin = 0, ymax = Signal, fill = factor(inst_frac))) +
    geom_line(aes(x = mL, y = Signal)) +
    facet_grid(Sample ~ ., scales = 'free')
  ggsave(filename = file.path(out.dir, paste('mAU_fractions_', no.ext, '.pdf', sep = '')), width = 6, height = 4)
}

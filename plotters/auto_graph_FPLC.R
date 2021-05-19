suppressMessages(library(tidyverse))

# 1 Import ----------------------------------------------------------------

# These values are all determined by options given to the python script.
# Use the simpler manual_plot_traces.R script if you're changing these.
args = commandArgs(trailingOnly = TRUE)
fractions <- as.integer(args[2]):as.integer(args[3])
low_ml <- as.integer(args[4])
high_ml <- as.integer(args[5])
out_dir <- args[6]
no_ext <- args[7]

data <- read_csv(args[1], col_types = 'ddffffd') %>%
  mutate(Fraction = as.factor(Fraction))

if (length(fractions) > 12) {
  color_scheme = scale_fill_discrete(limits = as.character(fractions), na.translate = FALSE)
} else {
  color_scheme <- scale_fill_manual(
    values = c(
      '#17becf', # cyan
      '#ff7f0e', # orange
      '#e377c2', # pink
      '#1f77b4', # blue
      '#2ca02c', # green
      '#d62728', # red
      '#9467bd', # purple
      '#7f7f7f', # grey
      '#bcbd22', # yellow-green
      '#8c564b', # brown
      'dark blue',
      'black'),
    limits = as.character(fractions))
}

# 2 Plot ------------------------------------------------------------------

# * 2.1 Multi-experiment plots --------------------------------------------

if (high_ml == 0) {
  low_ml = min(data$mL)
  high_ml = max(data$mL)
}

if (length(levels(factor(data$Sample))) > 1) {
data %>%
  filter(Channel == 'mAU' & mL > low_ml & mL < high_ml & Normalization == 'Signal') %>%
  group_by(Sample) %>%
  mutate(Normalized = ((Value - min(Value)) / (max(Value) - min(Value)))) %>%
  gather(key = Normalized, value = Value, Value, Normalized) %>%
  ungroup() %>%
  ggplot(aes(x = mL, y = Value, color = Sample)) +
  facet_grid(Normalized ~ ., scales = 'free') +
  theme_minimal() +
  color_scheme +
  geom_line()
ggsave(filename = file.path(out_dir, paste('all_samples_', no_ext, '.pdf', sep = '')), width = 8, height = 5)
} else {
  data %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10) & Normalization == 'Signal') %>%
    ggplot(aes(x = mL, y = Value, color = Channel)) +
    theme_minimal() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    color_scheme +
    geom_line()
  ggsave(filename = file.path(out_dir, paste('all_channels_', no_ext, '.pdf', sep = '')), width = 6, height = 4)
}

# * 2.2 mAU fraction plots ------------------------------------------------

if (length(fractions) == 1 & fractions[1] == 0) {
  data %>%
    filter(Channel == 'mAU' & Normalization == 'Signal') %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
    group_by(Sample) %>%
    ggplot() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    theme_minimal() +
    geom_line(aes(x = mL, y = Value)) +
    facet_grid(Sample ~ ., scales = 'free')
  ggsave(filename = file.path(out_dir, paste('mAU_', no_ext, '.pdf', sep = '')), width = 6, height = 4)
} else {
  data %>%
    filter(Channel == 'mAU' & Normalization == 'Signal') %>%
    filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
    group_by(Sample) %>%
    ggplot() +
    coord_cartesian(xlim = c(low_ml, high_ml)) +
    theme_minimal() +
    color_scheme +
    labs(fill = 'Fraction') +
    geom_ribbon(aes(x = mL, ymin = 0, ymax = Value, fill = Fraction)) +
    geom_line(aes(x = mL, y = Value))
  ggsave(filename = file.path(out_dir, paste('mAU_fractions_', no_ext, '.pdf', sep = '')), width = 6, height = 4)
}

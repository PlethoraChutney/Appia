library(tidyverse)
library(ggplot2)
library(devEMF)

# 1 Import ----------------------------------------------------------------

min_frac <- 10 # everything before this fraction will be 'Waste'
max_frac <- 20 # everything after this fraction will be 'Waste'
low_ml <- 5 # these values set the x-axis limits
high_ml <- 25

data <- read_csv('fplcs.csv', col_types = 'dcddcci') %>%
  mutate(inst_frac = if_else(inst_frac < min_frac, 'Waste', if_else(inst_frac > max_frac, 'Waste', as.character(inst_frac))))

# 2 Plot ------------------------------------------------------------------

data %>%
  filter(Channel == 'mAU') %>%
  filter(mL > (low_ml - 10) & mL < (high_ml + 10)) %>%
  group_by(Sample) %>%
  ggplot() +
  coord_cartesian(xlim = c(low_ml, high_ml)) +
  theme_minimal() +
  scale_fill_manual(values = c(
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
    'black'
  ), limits = min_frac : max_frac) +
  labs(fill = 'Fraction') +
  geom_ribbon(aes(x = mL, ymin = 0, ymax = Signal, fill = factor(inst_frac))) +
  geom_line(aes(x = mL, y = Signal))
ggsave(filename = 'manual_fplc.pdf', width = 6, height = 4)

library(tidyverse)

# 1 Common Modifications --------------------------------------------------

# fractions to highlight/fill
# to make a list in R, use c(item, item, item)
fractions <- c(10:15)

# these values set the x-axis limits
low_ml <- 5 
high_ml <- 25

# processed .csv file
filename <- Sys.glob('*_fplc.csv')[1]

# 2 Import ----------------------------------------------------------------

data <- read_csv(filename, col_types = 'ddffffd')

# 3 Color Scheme ----------------------------------------------------------
if (length(fractions) > 12) {
  color_scheme <- scale_fill_discrete(limits = as.character(fractions), na.translate = FALSE, na.value = 'transparent')
} else {
  color_scheme <- scale_fill_manual(
    values = c(
      '#1f77b4', # blue
      '#ff7f0e', # orange
      '#17becf', # cyan
      '#e377c2', # pink
      '#2ca02c', # green
      '#d62728', # red
      '#9467bd', # purple
      '#7f7f7f', # grey
      '#bcbd22', # yellow-green
      '#8c564b',  # brown
      'dark blue',
      'black'),
    limits = as.character(fractions), na.value = 'transparent')
}

# 4 Plot ------------------------------------------------------------------

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
ggsave(filename = 'manual_fplc.pdf', width = 6, height = 4)

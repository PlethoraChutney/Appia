library(tidyverse)


# 1 Import ----------------------------------------------------------------

long_trace_filename <- Sys.glob('*_hplc-long.csv')[1]

data <- read_csv(file = long_trace_filename) %>% 
  mutate(Channel = case_when(
    grepl('ex280/em350', Channel) ~ 'Trp',
    grepl('ex488/em509', Channel) ~ 'GFP',
    TRUE ~ as.character(Channel)
  ))

samples <- c(unique(data$Sample))
channels <- c(unique(data$Channel))
normalization <- c('Normalized', 'Signal')
x_limits <- c(NA, NA)
y_limits <- c(NA, NA)

# 2 Plot ------------------------------------------------------------------

if (length(unique(samples)) > 12) {
  color_scheme = scale_color_viridis_d()
} else {
  color_scheme = scale_color_manual(values = c(
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
    'black'
  )
  )
}


data %>%
  filter(Time > 0.5 & Sample %in% samples & Channel %in% channels & Normalization %in% normalization) %>%
  ggplot(aes(x = mL, y = Value)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  coord_cartesian(
    xlim = x_limits,
    ylim = y_limits
  ) +
  facet_grid(cols = vars(Channel), rows = vars(Normalization), scales = "free")
ggsave('fsec_traces.pdf', width = 7, height = 5)

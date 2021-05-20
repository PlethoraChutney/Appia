library(tidyverse)


# 1 Import ----------------------------------------------------------------

long_trace_filename <- Sys.glob('*_hplc-long.csv')[1]

channel_list <- list(
  'Trp' = '2475ChA ex280/em350',
  'GFP' = '2475ChB ex488/em509'
)

data <- read_csv(file = long_trace_filename, col_types = 'dffdfd') %>% 
  mutate(Channel = fct_recode(Channel, !!!channel_list))

# 2 Plot ------------------------------------------------------------------

if (length(levels(as.factor(data$Sample))) > 12) {
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
  filter(Time > 0.5) %>%
  ggplot(aes(x = mL, y = Value)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(cols = vars(Channel), rows = vars(Normalization), scales = "free")
ggsave('fsec_traces.pdf', width = 7, height = 5)

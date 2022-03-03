suppressWarnings(suppressMessages(library(tidyverse)))


# 1 Import ----------------------------------------------------------------

args = commandArgs(trailingOnly = TRUE)

data <- read.csv(file = args[1], header = TRUE) %>%
  mutate(Channel = if_else(grepl('ex280/em350', Channel), 'Trp',
                           if_else(grepl('ex488/em509', Channel), 'GFP', as.character(Channel)))) %>% 
  filter(Time > 0.5)

# 2 Plot ------------------------------------------------------------------

if (length(levels(as.factor(data$Sample))) > 12) {
  color_scheme = scale_color_viridis_d()
} else {
  color_scheme = scale_color_manual(
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
      'black'
    )
  )
}

data %>% 
  ggplot(aes(x = mL, y = Value)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(rows = vars(Normalization), cols = vars(Channel), scales = "free") +
  xlab("Volume (mL)") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.25)))

if (max(as.numeric(args[2:3])) == 0) {
  last_plot()
} else {
  last_plot() +
  coord_cartesian(xlim = as.numeric(args[2:3]))
}
ggsave('fsec_traces.pdf', width = 7, height = 5)

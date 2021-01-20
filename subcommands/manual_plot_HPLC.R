library(tidyverse)
library(ggplot2)


# 1 Import ----------------------------------------------------------------

long_trace_filename <- "long_chromatograms.csv"

data <- read.csv(file = long_trace_filename, header = TRUE) %>% 
  pivot_longer(cols = c(Signal, Normalized), names_to = 'Normalization', values_to = 'Signal')

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
  ggplot(aes(x = mL, y = Signal)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(Normalization ~ Channel, scales = "free") +
  xlab("Volume (mL)")
ggsave('fsec_traces.pdf', width = 7, height = 5)

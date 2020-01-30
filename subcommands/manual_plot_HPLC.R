library(tidyverse)
library(ggplot2)


# 1 Import ----------------------------------------------------------------

long_trace_filename = "long_chromatograms.csv"

data <- read.csv(file = long_trace_filename, header = TRUE) %>%
  group_by(Channel, Sample) %>%
  mutate(Normalized = (Signal-min(Signal))/(max(Signal) - min(Signal))) %>%
  ungroup() %>%
  mutate(Channel = if_else(grepl('ex280/em350', Channel), 'Trp',
                           if_else(grepl('ex488/em509', Channel), 'GFP', as.character(Channel)))) %>% 
  gather(key = Normalized, value = Signal, -Time, -Channel, -Sample)

# 2 Plot ------------------------------------------------------------------

if (length(levels(data$Sample)) > 10) {
  color_scale = scale_color_viridis_d()
} else {
  color_scale = scale_color_manual(values = c(
    '#17becf', # cyan
    '#ff7f0e', # orange
    '#e377c2', # pink
    '#1f77b4', # blue
    '#2ca02c', # green
    '#d62728', # red
    '#9467bd', # purple
    '#7f7f7f', # grey
    '#bcbd22', # yellow-green
    '#8c564b'  # brown
  )
  )
}

ggplot(data = data, aes(x = Time, y = Signal)) +
  theme_light() +
  color_scale +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  xlab("Time (minutes)") +
  ggtitle("FSEC Traces")
ggsave('fsec_traces.pdf', width = 7, height = 5)

data %>% 
  filter(Normalized == 'Normalized') %>% 
  ggplot(aes(x = Time, y = Signal)) +
  theme_light() +
  color_scale +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  xlab("Time (minutes)") +
  ylab("Normalized Signal") +
  ggtitle("Normalized FSEC Traces")
ggsave('normalized_traces.pdf', width = 7, height = 5)

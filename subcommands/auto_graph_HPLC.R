suppressWarnings(suppressMessages(library(dplyr)))
suppressWarnings(suppressMessages(library(stringr)))
suppressWarnings(suppressMessages(library(ggplot2)))


# 1 Import ----------------------------------------------------------------

long_trace_filename = "long_chromatograms.csv"
args = commandArgs(trailingOnly = TRUE)
setwd(args[1])
experiment_name = str_remove(basename(args[1]), '_processed')

data <- read.csv(file = long_trace_filename, header = TRUE) %>%
  group_by(Channel, Sample) %>%
  mutate(Normalized = (Signal-min(Signal))/(max(Signal) - min(Signal))) %>%
  ungroup() %>%
  mutate(Channel = if_else(grepl('ex280/em350', Channel), 'Trp',
                           if_else(grepl('ex488/em509', Channel), 'GFP', as.character(Channel))))

# 2 Plot ------------------------------------------------------------------

if (length(levels(data$Sample)) > 12) {
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
                       

ggplot(data = data, aes(x = Time, y = Signal)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  ggtitle(str_c(experiment_name, ' Raw Signal')) +
  xlab("Time (minutes)")
ggsave('fsec_traces.pdf', width = 7, height = 5)

ggplot(data = data, aes(x = Time, y = Normalized)) +
  theme_minimal() +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  xlab("Time (minutes)") +
  ggtitle(str_c(experiment_name, ' Normalized Signal')) +
  ylab("Normalized Signal")
ggsave('normalized_traces.pdf', width = 7, height = 5)

suppressWarnings(suppressMessages(library(dplyr)))
suppressWarnings(suppressMessages(library(stringr)))
suppressWarnings(suppressMessages(library(ggplot2)))


# 1 Import ----------------------------------------------------------------

long_trace_filename = "long_chromatograms.csv"
args = commandArgs(trailingOnly = TRUE)
setwd(args[1])
experiment_name = str_remove(basename(args[1]), '_processed')

data <- read.csv(file = long_trace_filename, header = TRUE) %>%
  mutate(Channel = if_else(grepl('ex280/em350', Channel), 'Trp',
                           if_else(grepl('ex488/em509', Channel), 'GFP', as.character(Channel)))) %>% 
  filter(Time > 0.5)

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
  ggplot(aes(x = mL, y = Signal)) +
  theme_minimal() +
  geom_vline(data = calibrations, aes(xintercept = mL), color = 'grey', linetype = 'dashed') +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(rows = vars(Channel), scales = "free") +
  xlab("Volume (mL)") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.25)))
ggsave('fsec_traces.pdf', width = 7, height = 5)

data %>% 
  ggplot(aes(x = mL, y = Normalized)) +
  theme_minimal() +
  geom_vline(data = calibrations, aes(xintercept = mL), color = 'grey', linetype = 'dashed') +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(rows = vars(Channel), scales = "free") +
  coord_cartesian(ylim = c(0, 1)) +
  ylab("Normalized Signal")
ggsave('normalized_traces.pdf', width = 7, height = 5)

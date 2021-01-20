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

cal_10_300 <- tibble(
    mL = c(3, 7, 14, 22),
    Size = c(100, 50, 25, 12)
  )
cal_5_150 <- tibble(
    mL = c(0.7, 1.2, 2, 2.1),
    Size = c(100, 50, 25, 12)
  )

if( max(data$mL) > 20) {
  calibrations <- cal_10_300
} else {
  calibrations <- cal_5_150
}

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
  scale_x_continuous('Volume (mL)', 
                     sec.axis = sec_axis(trans = ~.,
                                         name = 'Calibrations (MDa)',
                                         breaks = calibrations$mL,
                                         labels = calibrations$Size)
  ) +
  theme(axis.title.x.top = element_text(size = 8)) +
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
  scale_x_continuous('Volume (mL)', 
                     sec.axis = sec_axis(trans = ~.,
                                         name = 'Standards (MDa)',
                                         breaks = calibrations$mL,
                                         labels = calibrations$Size)
                     ) +
  theme(axis.title.x.top = element_text(size = 8)) +
  color_scheme +
  geom_line(aes(color = Sample)) +
  facet_grid(rows = vars(Channel), scales = "free") +
  coord_cartesian(ylim = c(0, 1)) +
  ylab("Normalized Signal")
ggsave('normalized_traces.pdf', width = 7, height = 5)

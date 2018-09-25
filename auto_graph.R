###### Preamble ######
library(dplyr)
library(ggplot2)

long_trace_filename = "long_chromatograms.csv"

###### Make Graphs ######
data <- read.csv(file = long_trace_filename, header = TRUE) %>%
  group_by(Channel, Sample) %>%                                         # group_by lets us keep channels separate
  mutate(Normalized = (Signal-min(Signal))/(max(Signal) - min(Signal))) # when we normalize with this function


cairo_pdf(filename = "fsec_traces.pdf", width = 7, height = 5)          # cairo_pdf is used in windows because the
ggplot(data = data, aes(x = Time, y = Signal)) +                        # default graphics are much uglier and have
  theme_light() +                                                       # some unexpected behaviors
  scale_color_viridis_d() +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  xlab("Time (minutes)") +
  ggtitle("FSEC Traces")
dev.off()

cairo_pdf(filename = "normalized_traces.pdf", width = 7, height = 5)
ggplot(data = data, aes(x = Time, y = Normalized)) +
  theme_light() +
  scale_color_viridis_d() +
  geom_line(aes(color = Sample)) +
  facet_grid(Channel ~ ., scales = "free") +
  xlab("Time (minutes)") +
  ylab("Normalized Signal") +
  ggtitle("Normalized FSEC Traces")
dev.off()

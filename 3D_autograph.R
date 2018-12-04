library(tidyverse)
library(ggplot2)

data <- read_csv('long_chromatograms.csv') 

tidy.data <- data %>% 
  gather(key = 'Emission', value = 'Signal', -Time, -Excitation, -Sample) %>% 
  drop_na(Signal) %>%
  mutate(Emission = as.numeric(Emission), Signal = as.numeric(Signal), Excitation = as.factor(Excitation), Sample = as.factor(Sample)) %>% 
  group_by(Excitation, Sample) %>% 
  mutate(Normalized = (Signal-min(Signal))/(max(Signal) - min(Signal))) %>% 
  ungroup()

plot <- tidy.data %>% 
  ggplot(aes(x = Time, y = Emission, z = Signal, fill = Signal)) +
  theme_dark() +
  geom_raster() +
  scale_fill_viridis_c(option = 'magma') +
  facet_grid(Sample ~ Excitation, scales = 'free')
  
norm.plot <- tidy.data %>% 
  ggplot(aes(x = Time, y = Emission, z = Normalized, fill = Normalized)) +
  theme_dark() +
  geom_raster() +
  scale_fill_viridis_c(option = 'magma') +
  facet_grid(Sample ~ Excitation, scales = 'free')

cairo_pdf(filename = '3D_plot.pdf', width = 8, height = 8)
plot
dev.off()

cairo_pdf(filename = 'normalized_3D_plot.pdf', width = 8, height = 8)
norm.plot
dev.off()
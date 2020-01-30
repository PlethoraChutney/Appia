library(tidyverse)
library(ggplot2)


# 1 Import ----------------------------------------------------------------

args = commandArgs(trailingOnly = TRUE)
setwd(args[1])

# column_spec is used to explicitely tell R which columns are doubles and which
# are character values. The value is printed by the python script --- you will
# need that value as it is different for each run. If you don't want to re-run
# the python script, you can make it yourself: 'dccc' then fill to the number
# of columns with 'd'.
column_spec <- args[2]

data <- read_csv('3D_chromatograms.csv', na = 'NA', col_types = column_spec)

#  * 1.1 Tidying ----------------------------------------------------------

try(
  tidy.emission.scan <- data %>%
    filter(Scan_Type == 'emission_scan') %>%
    gather(key = 'Emission', value = 'Signal', -Time, -Excitation, -Sample) %>%
    mutate(Emission = as.numeric(Emission), Signal = as.double(Signal), Excitation = as.factor(Excitation), Sample = as.factor(Sample)) %>%
    group_by(Excitation, Sample) %>%
    drop_na(Signal) %>%
    mutate(Normalized = ((Signal-min(Signal))/(max(Signal) - min(Signal)))) %>%
    ungroup()
)

try(
tidy.excitation.scan <- data %>%
  filter(Scan_Type == 'excitation_scan') %>%
  gather(key = 'Excitation', value = 'Signal', -Time, -Emission, -Sample) %>%
  mutate(Excitation = as.numeric(Excitation), Signal = as.double(Signal), Emission = as.factor(Emission), Sample = as.factor(Sample)) %>%
  drop_na(Signal) %>%
  group_by(Emission, Sample) %>%
  mutate(Normalized = (Signal-min(Signal))/(max(Signal) - min(Signal))) %>%
  ungroup()
)

# 2 Plotting --------------------------------------------------------------

if(exists('tidy.emission.scan')){
  em.plot <- tidy.emission.scan %>%
    ggplot(aes(x = Time, y = Emission, z = Signal, fill = Signal)) +
    theme_dark() +
    geom_raster() +
    scale_fill_viridis_c(option = 'magma') +
    ggtitle('Emission scan') +
    facet_grid(Sample ~ Excitation, scales = 'free')
  
  norm.em.plot <- tidy.emission.scan %>%
    ggplot(aes(x = Time, y = Emission, z = Normalized, fill = Normalized)) +
    theme_dark() +
    geom_raster() +
    scale_fill_viridis_c(option = 'magma') +
    ggtitle('Normalized emission scan') +
    facet_grid(Sample ~ Excitation, scales = 'free')
  
  ggsave('3D_em_plot.pdf', plot = em.plot, width = 8, height = 8, units = 'in')
  ggsave('norm_3D_em_plot.pdf', plot = norm.em.plot, width = 8, height = 8, units = 'in')
}

if (exists('tidy.excitation.scan')) {
  ex.plot <- tidy.excitation.scan %>%
    ggplot(aes(x = Time, y = Excitation, z = Signal, fill = Signal)) +
    theme_dark() +
    geom_raster() +
    scale_fill_viridis_c() +
    ggtitle('Excitation scan') +
    facet_grid(Sample ~ Emission, scales = 'free')

  norm.ex.plot <- tidy.excitation.scan %>%
    ggplot(aes(x = Time, y = Excitation, z = Normalized, fill = Normalized)) +
    theme_dark() +
    geom_raster() +
    scale_fill_viridis_c() +
    ggtitle('Normalized excitation scan') +
    facet_grid(Sample ~ Emission, scales = 'free')

  ggsave('3D_ex_plot.pdf', plot = ex.plot, width = 8, height = 8, units = 'in')
  ggsave('norm_3D_ex_plot.pdf', plot = norm.ex.plot, width = 8, height = 8, units = 'in')
}

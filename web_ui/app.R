library(tidyverse)
library(shiny)
library(ggplot2)

header.rows <- 2

rp.get.header <- function(arw) {
  header <- read_delim(arw, '\t', n_max = 1, col_types = 'cccc')
  head.list <- c(header$SampleName[1], header$Channel[1])
  return(head.list)
}

rp.get.trace <- function(arw) {
  trace <- read_delim(arw, '\t', skip = header.rows,col_names = c('Time', 'Signal'), col_types = 'nn')
}

rp.tidy.trace <- function(arw) {
  header <- rp.get.header(arw)
  trace <- rp.get.trace(arw)
  trace$Sample <- header[[1]]
  trace$Channel <- header[[2]]
  
  return(trace)
}

rp.collect.traces <- function(file.list) {
  trace.list <- map(file.list, rp.tidy.trace)
  collected.traces <- trace.list %>% 
    bind_rows() %>% 
    mutate(Sample = factor(Sample), Channel = factor(Channel)) %>% 
    group_by(Sample, Channel) %>% 
    mutate(Normalized = (Signal - min(Signal))/(max(Signal) - min(Signal))) %>% 
    ungroup()
  
  return(collected.traces)
}

rp.trace.dir <- function(directory) {
  
  already.processed <- file.path(directory, 'long_chromatograms.csv')
  
  if (file.exists(already.processed)) {
    collected.traces <- read_csv(already.processed, col_types = 'nncc') %>% 
      mutate(Sample = factor(Sample), Channel = factor(Channel)) %>% 
      group_by(Sample, Channel) %>% 
      mutate(Normalized = (Signal - min(Signal))/(max(Signal) - min(Signal))) %>% 
      ungroup()
    return(collected.traces)
  }
  
  
  file.list <- list.files(path = directory, pattern = '*.arw', full.names = TRUE)
  trace.data <- rp.collect.traces(file.list)
  
  return(trace.data)
}

rp.trace.plot <- function(dataframe, normalized, x_range = NULL, y_range = NULL) {
  if (!normalized) {
    return(
    ggplot(data = dataframe, aes(x = Time, y = Signal)) +
      theme_light() +
      scale_color_viridis_d() +
      coord_cartesian(xlim = x_range, ylim = y_range) +
      geom_line(aes(color = Sample)) +
      facet_grid(Channel ~ ., scales = "free") +
      xlab("Time (minutes)") +
      ggtitle("FSEC Traces")
    )
  }

  return(
    ggplot(data = dataframe, aes(x = Time, y = Normalized)) +
      theme_light() +
      scale_color_viridis_d() +
      coord_cartesian(xlim = x_range, ylim = y_range) +
      geom_line(aes(color = Sample)) +
      facet_grid(Channel ~ ., scales = "free") +
      xlab("Time (minutes)") +
      ggtitle("FSEC Traces")
  )
}

trace.data <- NULL
file.list <- list.dirs('..')
file.list <- file.list[!str_detect(file.list, pattern = '^../\\.')]

ui <- fluidPage(
  titlePanel('Trace Viewer', windowTitle = 'Baconguis Lab HPLC'),
  sidebarLayout(
    sidebarPanel(
      selectInput('runPicker', 'Pick a sample set', file.list),
      actionButton('loadData', 'Load data'),
      checkboxInput('normalized', 'Normalized'),
      checkboxGroupInput('tracePicker', 'Pick samples',
                         levels(trace.data$Sample), selected = trace.data$Sample
      ), 
      checkboxGroupInput('channelPicker', 'Pick channel(s)',
                         levels(trace.data$Channel), selected = trace.data$Channel
      ),
      checkboxInput('free_scales', 'Free Scales (disable range sliders)'),
      uiOutput('time_range'),
      uiOutput('signal_range')
    ),
    mainPanel(
      plotOutput('tracePlot', height = '800px')
    )
  )
)


server <- function(input, output, session) {
  observeEvent(input$loadData, {
    trace.data <- rp.trace.dir(input$runPicker)
    updateCheckboxGroupInput(session, 'tracePicker', 'Pick Sample(s)',
                             choices = levels(trace.data$Sample), selected = trace.data$Sample)
    updateCheckboxGroupInput(session, 'channelPicker', 'Pick channel(s)',
                             choices = levels(trace.data$Channel), selected = trace.data$Channel)
    output$time_range <- renderUI({
      minimum <- min(trace.data$Time)
      maximum <- max(trace.data$Time)
      sliderInput('x_range', 'Time (min)', min = minimum, max = maximum, value = c(minimum, maximum), step = 0.1)
    })
    output$signal_range <- renderUI({
      if (!input$normalized) {
        minimum <- min(trace.data$Signal)
        maximum <- max(trace.data$Signal)
        sliderInput('y_range', 'Signal', min = minimum, max = maximum, value = c(minimum, maximum), step = 10)
      }
      
      if (input$normalized) {
      minimum <- min(trace.data$Normalized)
      maximum <- max(trace.data$Normalized)
      }
      
      sliderInput('y_range', 'Signal', min = minimum, max = maximum, value = c(minimum, maximum), step = 0.1)
    })

  
  output$tracePlot <- renderPlot({
    input$loadData
    input$normalized
    input$free_scales
    
    if (!input$free_scales) {
    return(
    trace.data %>% 
      filter(Sample %in% input$tracePicker & Channel %in% input$channelPicker) %>% 
      rp.trace.plot(., input$normalized, input$x_range, input$y_range)
    )
    }
    
    if (input$free_scales) {
      return(
        trace.data %>% 
          filter(Sample %in% input$tracePicker & Channel %in% input$channelPicker) %>% 
          rp.trace.plot(., input$normalized)
      )
    }
  })
  })
}

shinyApp(ui = ui, server = server)

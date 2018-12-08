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
    mutate(Sample = factor(Sample), Channel = factor(Channel))
  
  return(collected.traces)
}

rp.trace.plot <- function(dataframe) {
  ggplot(data = dataframe, aes(x = Time, y = Signal)) +
    theme_light() +
    scale_color_viridis_d() +
    geom_line(aes(color = Sample)) +
    facet_grid(Channel ~ ., scales = "free") +
    xlab("Time (minutes)") +
    ggtitle("FSEC Traces")
}

rp.trace.dir <- function(directory) {
  file.list <- list.files(path = directory, pattern = '*.arw', full.names = TRUE)
  paste0(file.list)
  trace.data <- rp.collect.traces(file.list)
  
  return(trace.data)
}

trace.data <- NULL
file.list <- list.dirs() %>% as.tibble() %>% filter(value != '.')
file.list <- file.list$value

ui <- fluidPage(
  titlePanel('Trace Viewer', windowTitle = 'Baconguis Lab HPLC'),
  sidebarLayout(
    sidebarPanel(
      radioButtons('runPicker', 'Pick a sample set', file.list),
      actionButton('loadData', 'Load data'),
      checkboxGroupInput('tracePicker', 'Pick samples',
                         levels(trace.data$Sample), selected = trace.data$Sample
      ), 
      checkboxGroupInput('channelPicker', 'Pick channel(s)',
                         levels(trace.data$Channel), selected = trace.data$Channel
      )
    ),
    mainPanel(
      plotOutput('tracePlot')
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

  
  output$tracePlot <- renderPlot({
    input$loadData
    
    trace.data %>% 
      filter(Sample %in% input$tracePicker & Channel %in% input$channelPicker) %>% 
      rp.trace.plot()
  })
  })  
}

shinyApp(ui = ui, server = server)
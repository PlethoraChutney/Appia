# Waters HPLC Processing Scripts
This is a collection of scripts for quick analysis and plotting
of Waters liquid chromatography data. I expect that you'll run the
batch file from the same directory as the python and R scripts, as
well as your raw data (which are .arw files).

## How to format your Waters export method
I have dropped support for Waters data exported with long headers (i.e., two
  columns and multiple rows). These scripts now require your data to be formatted
  with a single pair of rows, with the columns deliniating what header goes where.

The 2D script requires `SampleName`, `Channel`, and `Sample Set Name`. The
3D script requires `SampleName`, `Instrument Method Name`, and `Sample Set Name`.
The order is not important, so long as the required headers are present in the .arw
file.

## What the scripts do
`export_script.bat` moves all .arw files into a directory, runs `assemble_rename_traces.py`,
renames the file to the date of the sample set, then runs the `auto_graph.R`.
Note that 3D files are also exported as .arw files, and this will not process them
correctly (or at all).

`assemble_rename_traces.py` produces a long-format table of all runs in the
directory. It also produces a wide-format table for use in non-R programs.

`auto_graph.R` produces the graphs. It produces a raw and normalized trace
for each channel, colored by sample.

Each of these three scripts has a 3D version, which are fundamentally different
in terms of data but basically identical in terms of process. The output is
obviously different, but the differences should be clear if you have a passing
understanding of what's going on with the data.

The 3D scripts will automatically determine if your samle was run with an excitation
or emission scan, separate the data into two groups, and plot each group independently.
This all relies on your instrument method containing _exactly one_ instance of the
pattern (without braces) `Scan{Ex|Em}{###}` where Ex or Em stands for excitation or
emission scan, and ### is the constant wavelength. So for example, if you
were scanning the emission while holding excitation constant at 540nm, your
instrument method needs the pattern `ScanEm540`.

## Web UI
The web ui (a [Shiny](https://shiny.rstudio.com/) app) provides a simpler way
to analyze the processed traces. Right now, only 2D data can be visualized with
this app. To launch it, run `launch_viewer.bat`.

Pick a trace folder from the dropdown menu (Simply a list of directories in the
parent directory), and hit `Load data`. A plot (or plots) will show up, basically
identical to the 2D exported plots. However, you can check or uncheck each sample
and channel, or normalize the data to the highest and lowest points, and the
plot will update in real time. The time slider sets min and max of the x-axis.

There is a y-slider, but it's hidden by default since typically
each channel has different relevant signal levels. Uncheck `Free Scales
(disable y-axis slider)` to set both y-axes equal and gain control of the scale.

You can export plots made with the Shiny app using the download plots button at
the bottom of the main panel.

# Waters HPLC Processing Scripts
This is a collection of scripts for quick analysis and plotting
of Waters liquid chromatography data. I expect that you'll run the
batch file from the same directory as the python and R scripts, as
well as your raw data (which are .arw files).

## How to format your Waters export method
The scripts in the repo are set up to parse my Waters files, which
are exported with the following headers in the following order:

| Column | 2D                     | 3D                     |
|--------|------------------------|------------------------|
| 1      | Sample Name            | Sample Set Name        |
| 2      | Channel                | Sample Set Start Date  |
| 3      | Sample Set Finish Date | Sample Name            |
| 4      | Sample Set Name        | Instrument Method Name |

Feel free to include more information, or put yours in a different order or layout,
in your header. Just be sure to update the position information in the preamble
to the appropriate python script.

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

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
`export_script.bat` simply runs `assemble_rename_traces.py`, which does all the
heavy lifting. This is to get around the fact that you can't make python scripts
executable in Windows.

`assemble_rename_traces.py` first moves all of the 'arw' files into a new directory,
where it reads them and creates two files: `long_chromatograms.csv` and `wide_chromatograms.csv`.
Finally, it runs `auto_graph.R` on `long_chromatograms.csv`.

`auto_graph.R` produces the graphs. It produces a raw and normalized trace
for each channel, colored by sample.

![Example 2D Trace](test_traces/2d_example_plot.png)

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

![Example 3D Trace](3D_test_traces/example_3D_plot.png)

The batch scripts live in the root directory, everything else is in `/scripts/`.

## Web UI
The new Web UI relies on a couchdb database running on your HPLC computer. The
`assemble_traces.py` script in `new-web-ui` adds the trace to your couchdb database
in addition to making the local `.csv`s. `app.py` is a plotly dash script that creates
a web interface where you can go through and find traces by typing in a dropdown and
interact with them directly. This is much faster than the old R solution, because
it doesn't have to re-draw graphs every time you change anything and it is reading
from a database instead of a file. Also much much cleaner and easier to style. Check
it out!

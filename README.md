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
The batch file moves all .arw files into a directory, runs the python script,
renames the file to the date of the sample set, then runs the R script.

The python file produces a long-format table of all runs in the directory. The
2D version also produces a wide-format table for use in non-R programs.

The R file produces the graphs. The 2D data produces a raw and normalized trace
for channel, colored by trace. The 3D data produces a set of heatmaps for each
sample and excitation wavelength.

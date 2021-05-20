# Appia - simple chromatography processing
Appia is a set of scripts to process and view chromatography data from AKTA, Shimadzu, and
Waters systems. Chromatography data can then be viewed on the easy-to-use and intuitive
web interface, built with [plotly dash](https://plotly.com/dash/).

Additionally, automatic plots will be prepared for all 
data using [ggplot](https://ggplot2.tidyverse.org/) in R. Options to copy a manual file for plot tweaking are
available.

## Installation
### Server installation
1. Install [docker](https://www.docker.com/)
2. Copy `docker-compose.yml` wherever you want the database to save data
3. Set the $COUCHDB_USER and $COUCHDB_PASSWORD environment variables (**in your environment!**)
4. Run `docker-compose up` in the same directory as docker-compose.yml

### Local/processing-only installation:
This process will install Python, R, and all the packages/libraries you need.
I highly recommend you use a virtual environment for the python packages. Conda
is also fine, but I'm trying to keep this as simple as possible.

1. Clone this repo (or if you don't have git installed, just download it)
2. Install [python](https://www.python.org/)
    1. Run `python -m virtualenv venv` (use python 3)
    2. Run `venv/Scripts/activate` (Windows) or `source venv/bin/activate` (Mac/Linux)
    3. Run `python -m pip install -r requirements.txt`
3. Install [R](https://www.r-project.org/)
    1. In an R session (R.exe/R for Windows/Mac) run:
    2. `install.packages('tidyverse')`
4. *(Optional) Install [R Studio](https://www.rstudio.com/) for easier use of the
    manual plot scripts*

## HPLC Processing
Appia reads `.arw` or `.asc` files (from Waters and Shimadzu HPLCs, respectively)
for information about the sample and how it was run, then optionally collects all the indicated
traces into an Experiment for upload to the visualization database.

### How to format your Waters export method
When exporting your data, please export the headers as two rows with multiple columns,
rather than two columns with multiple rows.

The 2D script requires `SampleName`, `Channel`, `Instrument Method Name` and
`Sample Set Name`. The 3D script requires `SampleName`, `Instrument Method
Name`, and `Sample Set Name`. The order is not important, so long as the
required headers are present in the .arw file. Other information can be there as
well, it won't hurt anything. You will also want to update the flow rates to
match your per-column flow rate. Your `Instrument Method` must contain either
`5_150` or `10_300` (for 5/150 and 10/300) columns. This can all be customized by
changing the `flow_rates` and `column_volumes` dictionaries at the top of
`processors/hplc.py`

If you are using a Shimadzu instrument, you've got a little less support than Waters.
Your method will need the standard headers, including `Sample ID:`,
`Total Data Points`, and `Sampling Rate:`. When you process, you will need
to pass a set of arguments to tell appia which channel corresponds to what,
since Shimadzu instruments only output a letter.

## AKTA FPLC Processing
The AKTA processing is straightforward. First, export your data from the AKTA in
.csv format. You'll have to open the trace in Unicorn and use the export button there,
just using "Export Data" saves a zipped binary which Appia can't read.
Then, run `appia.py fplc` on either one .csv file or a list of
.csv files.

## Web UI

When you
process HPLC and/or FPLC data with Appia, you create an Experiment. These Experiments
are then uploaded to a CouchDB server. The Appia web server pulls data from the
CouchDB to display traces using plotly dash. This is the main power of Appia --- you
can use your browser to quickly see your data, zoom in and out, select different
traces, combine experiments to compare different runs, re-normalize the data, and
share links with lab members.

### Uploading an Experiment
To upload an experiment, when you process it include the `-d` flag. This will
attempt to read the environment variables `$COUCHDB_USER`, `$COUCHDB_PASSWORD`,
and `$COUCHDB_HOST` and use those to upload the Experiment to the correct database.
You can also pass a JSON file to `-d` instead but you should never save passwords
in plaintext.

### Viewing the experiment
Simply navigate to your server and view the trace page. The docker default is
`myserver:8080/traces`. You can search
experiments in the dropdown menu and concatenate HPLC results to compare across
experiments. Clicking "Renormalize HPLC" will re-normalize the traces to set the
maximum of the currently-viewed unnormalized region to 1, allowing you to compare
specific peaks.

## Batch scripts
From the command line, the best way to use Appia is to run appia.py. However,
several batch scripts are included in this repo to give users who prefer not
to use command line interfaces a set of commonly-used optoins. You could write
equivalent shell scripts for Linux or Mac machines, but since most chromatography
systems run on Windows I've included these for those machines.

### process.bat
Read all files in the current directory and process all CSV, ASC, and ARW files
into a new experiment which is uploaded to the database using environment variables

### process-and-rename.bat
Same as above, but specify an Experiment ID yourself instead of reading one from
the data.

##### Preamble #####
import numpy as np
import pandas as pd
import sys
import os
import shutil
import subprocess
import argparse

# This script only works if you have your Empower method export the headers in
# wide format.

# header_rows tells the header funtcions how many rows to pull, and the data
# functions how many to skip. Since the data functions don't use headers, you
# actually want this to be one more than your real header rows.
header_rows = 2
directory_renamed = "renamed_traces"

# data_row tells the header functions where to look for actual values.
data_row = 0

##### Chromatogram Consolidation Functions #####

def get_file_list(directory):
	file_list = []
	for file in os.listdir(directory):
		if file.endswith(".arw"):
			file_list.append(os.path.join(directory, file))

	return file_list

# get_headers and get_chroms are for the wide data format
def get_headers(file_list):
	header_list = ["Time (minutes)"]
	for file in file_list:
		df = pd.read_csv(file, delim_whitespace = True, nrows = header_rows)
		header = [str(df.loc[data_row]['SampleName']) + " " + str(df.loc[data_row]['Channel'])]
		header_list.append(header[0])
	return(header_list)

def get_chroms(file_list, header_list):
	# get the time column from the first trace
	first_trace = pd.read_csv(file_list[1], delim_whitespace = True, skiprows = header_rows, names = ["Time", "Trace"], header = None)

	chroms = first_trace[["Time"]].copy()

	for file in file_list:
		df = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows, names = ["Time", "Trace"], header = None)
		chroms = pd.concat([chroms, df["Trace"]], axis = 1)

	chroms.columns = header_list
	return chroms

# append_chroms is for the long data format
def append_chroms(file_list) :
	chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])
	for file in file_list:
		to_append = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows, names = ["Time", "Signal"], header = None)
		sample_info = pd.read_csv(file, delim_whitespace = True, nrows = header_rows)
		sample_name = str(sample_info.loc[data_row]['SampleName'])
		channel_ID = str(sample_info.loc[data_row]['Channel'])
		to_append['Channel'] = channel_ID
		to_append['Sample'] = sample_name

		chroms = chroms.append(to_append, ignore_index = False)

	return chroms

def filename_human_readable(file_name):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows)
	readable_dir_name = str(headers.loc[data_row]['Sample Set Name']).replace('/', '-').replace(" ", "_") + "_processed"
	return readable_dir_name

##### Main #####

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description = 'A script to collect and plot Waters HPLC traces.')
	parser.add_argument('directory', default = os.getcwd(), help = 'Which directory to pull all .arw files from')
	parser.add_argument('-q', '--quiet', help = 'Don\'t print messages about progress', action = 'store_true', default = False)

	args = parser.parse_args()

	script_location = os.path.dirname(os.path.realpath(__file__))
	directory = os.path.normpath(args.directory)
	quiet = args.quiet

	if not quiet:
		print(f'Checking {directory} for .arw files...')

	file_list = get_file_list(directory)

	if len(file_list) == 0 and not quiet:
		print('No .arw files found. Exiting...')
		sys.exit(1)

	readable_dir = os.path.join(directory, filename_human_readable(file_list[0]))
	if not quiet:
		print(f'Found {len(file_list)} files. Moving to {readable_dir}...')

	new_fullpath = readable_dir
	os.makedirs(new_fullpath)

	for file in file_list:
		shutil.move(file, os.path.join(readable_dir, os.path.basename(file)))

	if not quiet:
		print('Assembling traces...')
	file_list = get_file_list(new_fullpath)
	header_list = get_headers(file_list)
	chroms = get_chroms(file_list, header_list)
	file_name = os.path.join(new_fullpath, 'wide_chromatograms.csv')
	chroms.to_csv(file_name, index = False)

	chroms = append_chroms(file_list)
	file_name = os.path.join(new_fullpath, 'long_chromatograms.csv')
	chroms.to_csv(file_name, index = False)

	if not quiet:
		print('Making plots...')
	subprocess.run(['Rscript', os.path.normpath(os.path.join(script_location, '..', 'scripts', 'auto_graph.R')), os.path.normpath(new_fullpath)])

	if not quiet:
		print('Done!')

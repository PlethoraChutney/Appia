#!/usr/bin/env python3
import numpy as np
import pandas as pd
import sys
import os
import shutil
import subprocess
import argparse

# 1 Import functions -----------------------------------------------------------

def get_file_list(directory):
	file_list = []
	for file in os.listdir(directory):
		if file.endswith(".arw"):
			file_list.append(os.path.join(directory, file))

	return file_list

# 2 Data processing functions --------------------------------------------------

def append_chroms(file_list, header_rows = 2, data_row = 0) :

	# header_rows tells the header funtcions how many rows to pull, and the data
	# functions how many to skip. Since the data functions don't use headers, you
	# actually want this to be one more than your real header rows.

	directory_renamed = "renamed_traces"

	chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])
	for file in file_list:
		to_append = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows, names = ["Time", "Signal"], header = None)
		sample_info = pd.read_csv(file, delim_whitespace = True, nrows = header_rows)
		sample_name = str(sample_info.loc[data_row]['SampleName'])
		channel_ID = str(sample_info.loc[data_row]['Channel'])
		to_append['Channel'] = channel_ID
		to_append['Sample'] = sample_name

		chroms = chroms.append(to_append, ignore_index = False)

	wide_table = chroms.copy()
	wide_table['Sample'] = wide_table['Sample'].astype(str) + ' ' + wide_table['Channel']
	wide_table.drop('Channel', axis = 1)
	wide_table = wide_table.pivot_table(
		index = 'Time',
		columns = 'Sample',
		values = 'Signal'
	)

	return (chroms, wide_table)

def filename_human_readable(file_name, header_rows = 2, data_row = 0):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows)
	readable_dir_name = str(headers.loc[data_row]['Sample Set Name']).replace('/', '-').replace(" ", "_") + "_processed"
	return readable_dir_name

# 2 Main -----------------------------------------------------------------------

def main(args):

	script_location = os.path.dirname(os.path.realpath(__file__))
	directory = os.path.abspath(args.directory)
	new_name = args.rename
	reduce = args.reduce
	quiet = args.quiet
	no_db = args.no_db
	no_plots = args.no_plots
	copy_manual = args.copy_manual

# * 2.1 Import files -----------------------------------------------------------

	if not quiet:
		print(f'Checking {directory} for .arw files...')

	file_list = get_file_list(directory)

	if len(file_list) == 0 and not quiet:
		print('No .arw files found. Exiting...')
		sys.exit(1)

	if new_name is not None:
		readable_dir = os.path.join(directory, new_name)
	else:
		readable_dir = os.path.join(directory, filename_human_readable(file_list[0]))

	if not quiet:
		print(f'Found {len(file_list)} files. Moving to {readable_dir}...')

	new_fullpath = readable_dir
	os.makedirs(new_fullpath)

	for file in file_list:
		shutil.move(file, os.path.join(readable_dir, os.path.basename(file)))

# * 2.2 Assemble .arw to .csv --------------------------------------------------

	if not quiet:
		print('Assembling traces...')

	file_list = get_file_list(new_fullpath)
	long_and_wide = append_chroms(file_list)
	file_name = os.path.join(new_fullpath, 'long_chromatograms.csv')
	long_and_wide[0].to_csv(file_name, index = False)
	file_name = os.path.join(new_fullpath, 'wide_chromatograms.csv')
	long_and_wide[1].to_csv(file_name, index = True)

# * 2.3 Add traces to couchdb --------------------------------------------------

	if not no_db:
		if not quiet:
			print('Adding experiment to visualization database...')

		from subcommands import backend, config
		db = backend.init_db(config.config)
		backend.collect_experiments(os.path.abspath(new_fullpath), db, quiet, reduce)

# * 2.4 Plot traces ------------------------------------------------------------

	if not no_plots:
		if not quiet:
			print('Making plots...')
		subprocess.run(['Rscript', os.path.join(os.path.normpath(script_location), 'auto_graph_HPLC.R'), os.path.normpath(new_fullpath)])

	if copy_manual:
		if not quiet:
			print('Copying manual R script...')
		shutil.copyfile(os.path.join(script_location, 'manual_plot_HPLC.R'), os.path.join(new_fullpath, 'manual_plot_HPLC.R'))


	if not quiet:
		print('Done!')

parser = argparse.ArgumentParser(description = 'A script to collect and plot Waters HPLC traces.', add_help=False)
parser.set_defaults(func = main)
parser.add_argument('directory', default = os.getcwd(), help = 'Which directory to pull all .arw files from')
parser.add_argument('-q', '--quiet', help = 'Don\'t print messages about progress', action = 'store_true', default = False)
parser.add_argument('-r', '--rename', help = 'Use a non-default name')
parser.add_argument('--reduce', help = 'Keep only one in REDUCE points, e.g., `--reduce 10` keeps only 1/10th of your points. Use if your dataset is very large and you do not need high temporal resolution.', default = 1, type = int)
parser.add_argument('--no-db', help = 'Do not add to couchdb', action = 'store_true', default = False)
parser.add_argument('--no-plots', help = 'Do not make R plots', action = 'store_true', default = False)
parser.add_argument('--copy-manual', help = 'Copy R plot file for manual plot editing', action = 'store_true', default = False)

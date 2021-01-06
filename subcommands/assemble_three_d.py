import numpy as np
import pandas as pd
import sys
import os
import re
import shutil
import logging
import subprocess
import argparse

# 2 Consolidation Functions ----------------------------------------------------
def get_file_list(directory):
	file_list = []
	for file in os.listdir(directory):
		if file.endswith(".arw"):
			file_list.append(os.path.join(directory, file))

	return file_list

def append_chroms(file_list, excitation_regex = '(?<=ScanEx).{3}', emission_regex = '(?<=ScanEm).{3}', data_row = 0, header_rows = 2) :
	chroms = pd.DataFrame()

	for file in file_list:
		to_append = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows)
		sample_info = pd.read_csv(file, delim_whitespace = True, nrows = header_rows - 1)
		sample_name = str(sample_info.loc[data_row]['SampleName'])
		method_name = str(sample_info.loc[data_row]['Instrument Method Name'])

		excitation = re.search(excitation_regex, method_name)
		if (excitation):
			excitation = excitation.group(0)

		emission = re.search(emission_regex, method_name)
		if (emission):
			emission = emission.group(0)

		to_append['Sample'] = sample_name
		if (excitation):
			to_append['Excitation'] = excitation
			to_append['Scan_Type'] = 'emission_scan'
		if (emission):
			to_append['Emission'] = emission
			to_append['Scan_Type'] = 'excitation_scan'

		# Waters exports data as a header (Wavelength, [list of wavelenghts])
		# Followed by an empty row called Time (the real header for the first column)
		to_append.drop([0], inplace = True)
		to_append.rename(columns = {'Wavelength' : 'Time'}, inplace = True)

		chroms = chroms.append(to_append, ignore_index = False, sort = False)

	# move non-double columns up to the front using list comprehension
	chroms = chroms[[c for c in chroms if c in ['Time', 'Wavelength', 'Excitation', 'Emission', 'Sample', 'Scan_Type']] + [c for c in chroms if c not in ['Time', 'Wavelength', 'Excitation', 'Emission', 'Sample', 'Scan_Type']]]

	# column_spec will be used by R to explicitely declare which columns are what type of data
	column_spec = 'dccc' + 'd'*(len(chroms.columns)-4)
	return [chroms, column_spec]

def filename_human_readable(file_name, data_row = 0, header_rows = 2):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows - 1)
	readable_dir_name = str(headers.loc[data_row]['Sample Set Name']).replace('/', '-').replace(" ", "_") + "_processed"
	return readable_dir_name

# 3 Main -----------------------------------------------------------------------

def main(args):

	script_location = os.path.dirname(os.path.realpath(__file__))
	directory = os.path.normpath(args.directory)

	script_location = os.path.dirname(os.path.realpath(__file__))

	logging.info(f'Checking {directory} for .arw files...')
	file_list = get_file_list(directory)
	readable_dir = filename_human_readable(file_list[0])
	logging.info(f'Found {len(file_list)} files. Moving to {readable_dir}...')

	os.makedirs(os.path.join(directory, readable_dir))
	new_fullpath = os.path.join(directory, readable_dir)

	for file in file_list:
		shutil.move(file, new_fullpath)

	logging.info('Assembling traces...')
	file_list = get_file_list(new_fullpath)
	chroms, column_spec = append_chroms(file_list)
	file_name = os.path.join(new_fullpath, "3D_chromatograms.csv")
	chroms.to_csv(file_name, index = False)

	logging.info(f'Making plots using command: \n 3D_autograph {os.path.normpath(new_fullpath)} {column_spec}')
	subprocess.run(['Rscript', os.path.join(script_location, '3D_auto_graph_HPLC.R'), os.path.normpath(new_fullpath), column_spec])

parser = argparse.ArgumentParser(description = 'A script to collect and plot Waters 3D HPLC traces.', add_help=False)
parser.set_defaults(func = main)
parser.add_argument('directory', default = os.getcwd(), help = 'Which directory to pull all .arw files from')

##### Preamble #####

import numpy as np
import pandas as pd
import sys
import os
import re
import shutil
import subprocess

# This script only supports sample headers in the wide format

# header_rows should include the header AND the information of that header
# i.e., if your first row is "SampleName ..." and your second is "Buffer ..."
# header_rows is 2
header_rows = 2
directory_renamed = "renamed_traces"

# data_row is the row, *ignoring headers* in which values are stored. In the
# above example, data_row is 0
data_row = 0

# This is a positive lookbehind assertion, meaning it'll only match 3 characters
# preceeded by 'ScanEx' or 'ScanEm'. Please include this phrase in your methods if you want
# to use this script.
excitation_regex = '(?<=ScanEx).{3}'
emission_regex = '(?<=ScanEm).{3}'

##### Chromatogram Consolidation Functions #####
def get_file_list(directory):
	file_list = []
	for file in os.listdir(directory):
		if file.endswith(".arw"):
			file_list.append(os.path.join(directory, file))

	return file_list

def append_chroms(file_list) :
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

	return chroms

def filename_human_readable(file_name):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows - 1)
	readable_dir_name = str(headers.loc[data_row]['Sample Set Name']).replace('/', '-').replace(" ", "_") + "_processed"
	return readable_dir_name

##### Main #####

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("Assemble 3D chromatography data.\nUsage: python 3D_assemble_traces.py [trace_directory]")
	else:
		directory = sys.argv[1]
		file_list = get_file_list(directory)
		readable_dir = filename_human_readable(file_list[0])
		os.makedirs(os.path.join(directory, readable_dir))
		new_fullpath = os.path.join(directory, readable_dir)

		for file in file_list:
			shutil.move(file, os.path.join(new_fullpath, file))

		file_list = get_file_list(new_fullpath)
		chroms = append_chroms(file_list)
		file_name = os.path.join(new_fullpath, "3D_chromatograms.csv")
		chroms.to_csv(file_name, index = False)

		subprocess.run(['Rscript', os.path.join('scripts', '3D_autograph.R'), os.path.normpath(new_fullpath)])

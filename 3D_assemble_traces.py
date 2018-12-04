##### Preamble #####

import numpy as np
import pandas as pd
import sys
import os
import re

# if you make your own export method (in empower) that doesn't have the channel
# and sample names in the same place, change the rows below.
#
# don't forget that python is zero-indexed
# i.e., if you want to select the upper-left-most cell, that's column 0, row 0.
# cell B1 is column 1, row 0, etc.

name_column = 2
name_row = 1

date_column = 1
date_row = 1

sample_set_column = 0
sample_set_row = 1

method_name_column = 3
method_name_row = 1

header_rows = 2
directory_renamed = "renamed_traces"

# This is a positive lookbehind assertion, meaning it'll only match 3 characters
# preceeded by 'ScanEx'. Please include this phrase in your methods if you want
# to use this script.
excitation_regex = '(?<=ScanEx).{3}'

##### Chromatogram Consolidation Functions #####
# make a list of all paths to *.arw files in the given directory
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
		sample_info = pd.read_csv(file, delim_whitespace = True, nrows = header_rows, header = None)
		sample_name = str(sample_info.iloc[name_row,name_column])

		method_name = str(sample_info.iloc[method_name_row, method_name_column])
		excitation = re.search(excitation_regex, method_name).group(0)

		to_append['Excitation'] = excitation
		to_append['Sample'] = sample_name

		# Waters exports data as a header (Wavelength, [list of wavelenghts])
		# Followed by an empty row called Time (the real header for the first column)
		to_append.drop([0], inplace = True)
		to_append.rename(columns = {'Wavelength' : 'Time'}, inplace = True)

		chroms = chroms.append(to_append, ignore_index = False, sort = False)

	return chroms

def filename_human_readable(directory, file_name):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows, header = None)
	readable_dir_name = str(headers.iloc[sample_set_row, sample_set_column]).replace('/', '-').replace(" ", "_") + "_processed" #+ "_[" + str(headers.iloc[date_row, date_column]).replace('/', '-').replace(" ", "_") + "]_processed"
	return readable_dir_name

# def rename_traces(directory, renamed, file_list):           # Arpita likes to have the traces with sample name in them, rather than Waters's unique identifier
# 	for_renamed = os.path.join(directory, renamed)          # Keep in mind that if you somehow end up with two sample name/channel name pairs that are the same,
# 	if not os.path.exists(for_renamed):                     # this format won't work but the unique ID will. That's why the other functions don't use
# 		os.makedirs(for_renamed)                            # these renamed files.
#
# 	for file in file_list:
# 		chrom = pd.read_csv(file, delim_whitespace = True, header = None)
# 		filename = os.path.join(for_renamed, (str(chrom.iloc[name_row, name_column]) + "_" + str(chrom.iloc[channel_row, channel_column]).replace('/', '-').replace(" ", "_")) + ".csv")
# 		chrom.to_csv(filename, index = False, header = None)


##### Main #####

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("This script assembles Waters chromatograms.\nUsage: python assemble_rename_traces.py [trace_directory]")
	else:
		directory = sys.argv[1]
		file_list = get_file_list(directory)

		chroms = append_chroms(file_list)
		file_name = directory + "long_chromatograms.csv"
		chroms.to_csv(file_name, index = False)

		print(filename_human_readable(directory, file_list[0]))

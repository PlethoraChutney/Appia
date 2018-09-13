##### Preamble #####

import numpy as np
import pandas as pd
import sys
import os

# if you make your own export method (in empower) that doesn't have the channel and sample names in the same place, change the rows below.
#
# don't forget that python is zero-indexed
# i.e., if you want to select the upper-left-most cell, that's column 0, row 0. cell B1 is column 1, row 0, etc.

name_column = 0
name_row = 1

channel_column = 1
channel_row = 1

date_column = 2
date_row = 1

sample_set_column = 3
sample_set_row = 1

header_rows = 2
directory_renamed = "renamed_traces"


##### Chromatogram Consolidation Functions #####

def get_file_list(directory):                                # make a list of all paths to *.arw files in the given directory
	file_list = []
	for file in os.listdir(directory):
		if file.endswith(".arw"):
			file_list.append(os.path.join(directory, file))

	return file_list

def get_headers(file_list):                                  # get_headers() and get_chroms() are a dumb way to get the sample and channel for each .arw file
	header_list = ["Time (minutes)"]                         # if you ever want to rewrite something, these are probably the first things
	for file in file_list:
		df = pd.read_csv(file, delim_whitespace = True, nrows = header_rows, header = None)
		header = [str(df.iloc[name_row,name_column]) + " " + str(df.iloc[channel_row,channel_column])]      
		header_list.append(header[0])                               
	return(header_list)

def get_chroms(file_list, header_list):                     # pull traces from .arw files
	# get the time column from the first trace
	first_trace = pd.read_csv(file_list[1], delim_whitespace = True, skiprows = header_rows, names = ["Time", "Trace"], header = None)
	
	chroms = first_trace[["Time"]].copy()

	for file in file_list:
		df = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows, names = ["Time", "Trace"], header = None)
		chroms = pd.concat([chroms, df["Trace"]], axis = 1)

	chroms.columns = header_list
	return chroms

def append_chroms(file_list) :                              # a much smarter (written later) way of getting channel, sample, trace, and time for each .arw file in long form
	chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

	for file in file_list:
		to_append = pd.read_csv(file, delim_whitespace = True, skiprows = header_rows, names = ["Time", "Signal"], header = None)
		sample_info = pd.read_csv(file, delim_whitespace = True, nrows = header_rows, header = None)
		sample_name = str(sample_info.iloc[name_row,name_column])
		channel_ID = str(sample_info.iloc[channel_row,channel_column])
		to_append['Channel'] = channel_ID
		to_append['Sample'] = sample_name

		chroms = chroms.append(to_append, ignore_index = False)

	return chroms

def filename_human_readable(directory, file_name):
	headers = pd.read_csv(file_name, delim_whitespace = True, nrows = header_rows, header = None)
	readable_dir_name = str(headers.iloc[sample_set_row, sample_set_column]).replace('/', '-').replace(" ", "_") + "_processed" #+ "_[" + str(headers.iloc[date_row, date_column]).replace('/', '-').replace(" ", "_") + "]_processed"
	return readable_dir_name

def rename_traces(directory, renamed, file_list):           # Arpita likes to have the traces with sample name in them, rather than Waters's unique identifier
	for_renamed = os.path.join(directory, renamed)          # Keep in mind that if you somehow end up with two sample name/channel name pairs that are the same,
	if not os.path.exists(for_renamed):                     # this format won't work but the unique ID will. That's why the other functions don't use
		os.makedirs(for_renamed)                            # these renamed files.

	for file in file_list:
		chrom = pd.read_csv(file, delim_whitespace = True, header = None)
		filename = os.path.join(for_renamed, (str(chrom.iloc[name_row, name_column]) + "_" + str(chrom.iloc[channel_row, channel_column]).replace('/', '-').replace(" ", "_")) + ".csv")
		chrom.to_csv(filename, index = False, header = None)


##### Main #####

if __name__ == '__main__':
	if len(sys.argv) != 2:
		print("This script assembles Waters chromatograms.\nUsage: python assemble_rename_traces.py [trace_directory]")
	else:
		directory = sys.argv[1]
		file_list = get_file_list(directory)
		header_list = get_headers(file_list)
		chroms = get_chroms(file_list, header_list)
		file_name = directory + "wide_chromatograms.csv"
		chroms.to_csv(file_name, index = False)

		chroms = append_chroms(file_list)
		file_name = directory + "long_chromatograms.csv"
		chroms.to_csv(file_name, index = False)

		#rename_traces(directory, directory_renamed, file_list)

		with open("temp.txt", "w") as text_file:
			rename_command = filename_human_readable(directory, file_list[0])
			text_file.write(rename_command)
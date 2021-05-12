import pandas as pd
import numpy as np
import os
import shutil
import subprocess
import logging
from .core import *
from .experiment import Experiment

flow_rates = {
    '10_300': 0.5,
    '5_150': 0.3
}

column_volumes = {
    '10_300': 24,
    '5_150': 3
}


def append_waters(file_list):

    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    for i in range(len(file_list)):
        loading_bar(i, (len(file_list) - 1))
        file = file_list[i]
        to_append = pd.read_csv(
				file,
				delim_whitespace = True,
				skiprows = 2,
				names = ["Time", "Signal"],
				header = None,
				dtype = {'Time': np.float32, 'Signal': np.float32}
			)
        if to_append.shape[0] == 0:
            logging.error(f'File {file} is empty. Ignoring that file.')
            continue
        sample_info = pd.read_csv(
            file,
            delim_whitespace = True,
            nrows = 2,
            dtype = str
        )

        # pull sample info from the headers (in a separate df since the shape
        # is inconsistent). Then add the data

        sample_name = str(sample_info.loc[0]['SampleName'])
        channel_ID = str(sample_info.loc[0]['Channel'])
        to_append['Channel'] = channel_ID
        to_append['Sample'] = sample_name

        if 'Instrument Method Name' in sample_info:
            method = str(sample_info.loc[0]['Instrument Method Name'])

            # Here's where we look up methods. If you're not using per-column
            # methods, you'll have to change this and the above dict
            if '10_300' in method:
                column = '10_300'
            elif '5_150' in method:
                column = '5_150'

            to_append['mL'] = to_append['Time']*flow_rates[column]
            to_append['Column Volume'] = to_append['mL']/column_volumes[column]

        chroms = chroms.append(to_append, ignore_index = False)

    return chroms

def append_shim(file_list, channel_mapping):
    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    channel_names = list(channel_mapping.keys())

    for i in range(len(file_list)):

        loading_bar(i, (len(file_list) - 1))
        file = file_list[i]

        to_append = pd.read_csv(
            file,
            sep = '\t',
            skiprows = 16,
            names = ['Signal'],
            header = None,
            dtype = np.float32
        )

        sample_info = pd.read_csv(
            file,
            sep = '\t',
            nrows = 16,
            names = ['Stat'] + channel_names + ['Units'],
            engine = 'python'
        )

        sample_info.set_index('Stat', inplace = True)

        number_samples = int(sample_info.loc['Total Data Points:'][0])
        sampling_interval = float(sample_info.loc['Sampling Rate:'][0])
        seconds_list = [x * sampling_interval for x in range(number_samples)] * len(channel_names)

        to_append['Sample'] = str(sample_info.loc['Sample ID:'][0])
        to_append['Channel'] = [x for x in channel_names for i in range(number_samples)]
        to_append['Time'] = [x/60 for x in seconds_list]

        # this is obviously not strictly true
        if to_append.Time.max() < 20:
            column = '5_150'
        else:
            column = '10_300'

        to_append['mL'] = to_append['Time']*flow_rates[column]
        to_append['Column Volume'] = to_append['mL']/column_volumes[column]

        chroms = chroms.append(to_append, ignore_index = True, sort = True)

    chroms = chroms[['Time', 'Signal', 'Channel', 'Sample']]
    chroms = chroms.replace(channel_mapping)
    

    return chroms

def make_experiment(df, id, norm_range = None):
    df = df.groupby(['Sample', 'Channel']).apply(lambda x: normalizer(x, norm_range))
    df = df.melt(
        id_vars = ['mL', 'Sample'],
        value_vars = ['Signal', 'Normalized'],
        var_name = 'Normalization',
        value_name = 'Value'
    )

    if exp is None:
        exp = Experiment(id)

    exp.hplc = df

    return exp
import pandas as pd
import numpy as np
import sys
import json
import os
import logging
import re
from .core import loading_bar, normalizer

def get_flow_rate(flow_rate, method):
    # If user provides in argument we don't need to do this
    if flow_rate:
        return flow_rate
    
    # Open flow-rates JSON
    if method:
        # Open flow-rates JSON
        script_location = os.path.dirname(os.path.realpath(__file__))
        try:
            with open(os.path.join(script_location, 'flow_rates.json')) as fr:
                flow_rates = json.load(fr)

            match = False
            for key in flow_rates:
                if key in method:
                    if match:
                        logging.error('Multiple matches in flow_rates JSON!')
                        match = False
                        break
                    else:
                        match = True
                        flow_rate = flow_rates[key]

            if match:
                return flow_rate
        except FileNotFoundError:
            logging.warning('No flow_rates JSON found.')
    
    flow_rate = float(input(f'Flow rate (mL/min):'))
    return flow_rate


def append_waters(file_list, flow_rate = None):

    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    for i in range(len(file_list)):
        loading_bar(i+1, (len(file_list)), extension = ' Waters files')
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
            logging.warning(f'File {file} is empty. Ignoring that file.')
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
        try:
            set_name = str(sample_info.loc[0]['Sample Set Name'])
        except KeyError:
            logging.error('\nNo Sample Set Name found in arw file')
            set_name = None
        to_append['Channel'] = channel_ID
        to_append['Sample'] = sample_name


        if 'Instrument Method Name' in sample_info:
            method = str(sample_info.loc[0]['Instrument Method Name'])
        else:
            method = False
        flow_rate = get_flow_rate(flow_rate, method)

        to_append['mL'] = to_append['Time']*flow_rate

        chroms = chroms.append(to_append, ignore_index = False)

    chroms = chroms.groupby(['Sample', 'Channel']).apply(normalizer)
    chroms = chroms.melt(
        id_vars = ['mL', 'Sample', 'Channel', 'Time'],
        value_vars = ['Signal', 'Normalized'],
        var_name = 'Normalization',
        value_name = 'Value'
    )

    return chroms, set_name

def append_shim(file_list, channel_mapping, flow_rate = None):
    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    channel_names = list(channel_mapping.keys())

    for i in range(len(file_list)):

        loading_bar(i+1, (len(file_list)), extension = ' Shimadzu files')
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
        set_name = str(sample_info.loc['Acquisition Date and Time:'][0]).replace('/', '-').replace(' ', '_').replace(':', '-')

        to_append['Sample'] = str(sample_info.loc['Sample ID:'][0])
        to_append['Channel'] = [x for x in channel_names for i in range(number_samples)]
        to_append['Time'] = [x/60 for x in seconds_list]

        flow_rate = get_flow_rate(flow_rate, None)
        to_append['mL'] = to_append['Time'] * flow_rate

        chroms = chroms.append(to_append, ignore_index = True, sort = True)

    chroms = chroms[['Time', 'Signal', 'Channel', 'Sample', 'mL']]
    chroms = chroms.replace(channel_mapping)

    chroms = chroms.melt(
        id_vars = ['mL', 'Sample', 'Channel', 'Time'],
        value_vars = 'Signal',
        var_name = 'Normalization',
        value_name = 'Value'
    )

    return chroms, set_name

def append_agilent(file_list, flow_rate = None, channel_mapping = None):
    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    for i in range(len(file_list)):

        loading_bar(i+1, (len(file_list)), extension = ' Agilent files')
        file = file_list[i]

        to_append = pd.read_csv(
            file,
            sep = '\t',
            names = ['Time', 'Signal'],
            engine = 'python',
            encoding = 'utf_16'
        )

        sample_name = file.replace('.CSV', '').replace('_RT', '')

        channel = False
        if channel_mapping:
            channel = channel_mapping
        else:
            channel_reg = r'Channel[0-9]{3}'
            channel_regex = re.match(channel_reg, sample_name)
            if channel_regex:
                sample_name = re.sub(channel_reg, '', sample_name)
                try:
                    # pull the last three characters of the matching regex and check if they're an int
                    channel = channel_regex.group(0)[-3:]
                    int(channel)
                except ValueError:
                    logging.debug(f'Bad channel pattern in file {file}: channel')
                    channel = False
            
            if not channel:
                channel = input(f'Please provide a channel name for {file}:\n')
                if input('Set channel to "{channel}" for remaining Agilent files? Y/N\n').lower() == 'y':
                    channel_mapping = channel

        to_append.Sample = sample_name
        to_append.Channel = channel

        if not flow_rate:
            flow_reg = r'Flow[0-9]*\.[0-9]*'
            
            
        to_append['mL'] = to_append['Time'] * flow_rate
        


    sys.exit()

import pandas as pd
import numpy as np
from io import StringIO
import json
import os
import logging
import re
from appia.processors.core import loading_bar, normalizer
from appia.processors.gui import user_input

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
    
    flow_rate = float(user_input('Flow rate (mL/min):'))
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
        channel_ID = re.sub('2475Ch[A-D] ', '', str(sample_info.loc[0]['Channel']))
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

        chroms = pd.concat([chroms, to_append], ignore_index = True)

    chroms = chroms.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
    chroms = chroms.melt(
        id_vars = ['mL', 'Sample', 'Channel', 'Time'],
        value_vars = ['Signal', 'Normalized'],
        var_name = 'Normalization',
        value_name = 'Value'
    )

    return chroms, set_name

def get_shim_data(file, channel_names = None, flow_rate = None):
    with open(file, 'r') as f:
        first_line = f.readline().strip()

    if first_line == '[Header]':
        return new_shim_reader(file, channel_names, flow_rate)
    else:
        return old_shim_reader(file, channel_names, flow_rate)

# Very old shimadzu exports are much simpler than modern ones
def old_shim_reader(file, channel_names, flow_rate = None):
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

    return (to_append, set_name)

def new_shim_reader(file, channel_names = None, flow_rate = None):
    # new shimadzu tables are actually several tables separated by
    # headers, which are in the format `[header]`
    to_append = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample', 'mL'])

    with open(file, 'r') as f:
        tables = {}
        curr_table = False
        for line in f:
            if re.match('\[.*\]', line):
                curr_table = line.replace('[', '').replace(']', '').strip()
            else:
                if curr_table not in tables:
                    tables[curr_table] = [line]
                else:
                    tables[curr_table].append(line)

        # Get sample name
        for line in tables['Sample Information']:
            if 'Sample Name' in line:
                sample_name = line.strip().split('\t')[1]
            elif 'Sample ID' in line:
                try:
                    sample_id = line.strip().split('\t')[1]
                except IndexError:
                    sample_id = ''
        


        if sample_name != sample_id and sample_id != '':
            sample = sample_name + "_" + sample_id
        else:
            sample = sample_name
        logging.debug(sample)

        # Get sample set name
        for line in tables['Original Files']:
            if 'Batch File' in line:
                batch_path = line.strip().split('\t')[1]
        logging.debug(batch_path)
        sample_set = os.path.split(batch_path)[1][:-4]


        # Get detectors and channels
        for line in tables['Configuration']:
            if 'Detector ID' in line:
                detectors = line.strip().split('\t')[1:]
            elif 'Detector Name' in line:
                channels = line.strip().split('\t')[1:]

        det_to_channel = {}
        for i in range(len(detectors)):
            det_to_channel[detectors[i]] = channels[i]

        # Get all chromatograms
        chroms = []
        for key in tables:
            if re.match('LC Chromatogram', key):
                chroms.append(tables[key])

        channel_index = -1
        for chrom in chroms:
            channel_index += 1
            info_lines = chrom[:15]
            info = {}
            info_patterns = {
                'interval': 'Interval(msec)',
                'num_samples': '# of Points',
                'ex': 'Ex\. Wavelength',
                'em': 'Em\. Wavelength'
            }
            for key in info_patterns:
                for line in info_lines:
                    if re.match(info_patterns[key], line):
                        info[key] = line.strip().split('\t')[1]
                    elif re.match('R\.Time', line):
                        skip = info_lines.index(line) + 1
            
            df = pd.read_csv(
                StringIO(''.join(chrom)),
                sep = '\t',
                skiprows = skip,
                names = ['Time', 'Signal']
            )
            if 'ex' in info:
                df['Channel'] = f'Ex:{info["ex"]}/Em:{info["em"]}'
            else:
                df['Channel'] = channels[channel_index]
            df['Sample'] = sample
            
            to_append = pd.concat([to_append, df], ignore_index=True, sort = True)
            to_append['mL'] = to_append['Time'] * flow_rate

        return(to_append, sample_set)

def append_shim(file_list, channel_mapping, flow_rate = None):
    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample'])

    channel_names = list(channel_mapping.keys())
    flow_rate = get_flow_rate(flow_rate, None)

    for i in range(len(file_list)):

        loading_bar(i+1, (len(file_list)), extension = ' Shimadzu files')
        file = file_list[i]

        to_append, set_name = get_shim_data(file, channel_names, flow_rate)

        chroms = pd.concat([chroms, to_append], ignore_index = True, sort = True)

    chroms = chroms[['Time', 'Signal', 'Channel', 'Sample', 'mL']]
    chroms = chroms.replace(channel_mapping)

    chroms = chroms.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
    chroms = chroms.melt(
        id_vars = ['mL', 'Sample', 'Channel', 'Time'],
        value_vars = ['Signal', 'Normalized'],
        var_name = 'Normalization',
        value_name = 'Value'
    )

    return chroms, set_name

def append_agilent(file_list, flow_override = None, channel_override = None):
    chroms = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample', 'mL'])

    if channel_override:
        channel = channel_override
    else:
        channel = False

    if flow_override:
        flow_rate = flow_override
    else:
        flow_rate = False

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

        filename = os.path.split(file)[1]
        sample_name = filename.replace('.CSV', '').replace('_RT', '')


        # Channel
        if not channel_override:
            channel = False
        else:
            channel = channel_override
        
        if not channel:
            channel_reg = r'Channel[0-9]{3}'
            channel_search = re.search(channel_reg, sample_name)
            if channel_search:
                sample_name = re.sub(channel_reg, '', sample_name)
                try:
                    # pull the last three characters of the matching regex and check if they're an int
                    channel = channel_search.group(0)[-3:]
                    int(channel)
                except ValueError:
                    logging.debug(f'Bad channel pattern in file {file}: {channel}')
                    channel = False
            
            if not channel:
                channel = user_input(f'Please provide a channel name for {file}:\n')
                if user_input(f'Set channel to "{channel}" for remaining Agilent files? Y/N\n').lower() == 'y':
                    channel_override = channel
        to_append['Channel'] = channel


        # Flow rate
        if not flow_override:
            flow_rate = False
        else:
            flow_rate = flow_override

        if not flow_rate:
            i = 0
            while not flow_rate:
                if i == 0:
                    flow_reg = r'Flow[0-9]*\.[0-9]*'
                    flow_search = re.search(flow_reg, sample_name)

                    if flow_search:
                        sample_name = re.sub(flow_reg, '', sample_name)

                        try:
                            flow_rate = flow_search.group(0)[4:]
                            flow_rate = float(flow_rate)
                        except ValueError:
                            logging.debug(f'Bad flow rate pattern in file {file}: {flow_rate}')
                            flow_rate = False
                else:
                    try:
                        input_fr = user_input(f'Please provide a flow rate for {file} (mL/min)\n')
                        flow_rate = float(input_fr)
                        if user_input(f'Set flow rate to {flow_rate} for remaining Agilent files? Y/N\n').lower() == 'y':
                            flow_override = flow_rate
                    except ValueError:
                        logging.error('Flow rate must be a number')

                i += 1
            
        to_append['mL'] = to_append['Time'] * flow_rate

        # Set sample name down here so that flow and channel information have been removed
        to_append['Sample'] = sample_name

        chroms = pd.concat([chroms, to_append], ignore_index = True, sort = True)
        
    chroms = chroms.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
    chroms = chroms.melt(
        id_vars = ['mL', 'Sample', 'Channel', 'Time'],
        value_vars = 'Signal',
        var_name = 'Normalization',
        value_name = 'Value'
    )

    return chroms

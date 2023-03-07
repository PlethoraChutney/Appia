import pandas as pd
import numpy as np
from io import StringIO
import os
import logging
import re
from appia.processors.core import loading_bar, normalizer
from appia.processors.gui import user_input
from appia.parsers.user_settings import appia_settings

class HplcProcessor(object):
    """
    The parent processor for all Appia HPLC processing. Any
    processors should inherit from this class.
    flow_rate:  If a float is provided to this argument, it will
                stored in the _flow_rate attribute. This is the first
                place the get_flow_rate() method checks.
    df:         This attribute should return the standard dataframe.
                Implementation of this is left to each processor, since
                some manufacturers use multiple channels per file, etc.
    claim_file: this class method should return True if the processor
                thinks it is capable of processing a file and False otherwise
    prepare_sample: this method is called during __init__, and should
                collect all information about the sample necessary to
                process the actual trace data
    process_file: this method is calle during __init__ after prepare_sample()
                and should produce the dataframe
    """
    def __init__(self, filename, **kwargs):
        self.__class__.flow_rate_override = None
        self.filename = filename
        self.manufacturer = None
        self.method = None
        self.flow_rate = kwargs.get('flow_rate')
        self.__dict__.update(**kwargs)

        self.prepare_sample()
        self.process_file()

    @classmethod
    def claim_file(cls, filename):
        pass

    def prepare_sample(self):
        pass

    def process_file(self):
        pass
    
    @property
    def flow_rate(self) -> float:
        if self._flow_rate is not None:
            return self._flow_rate
        else:
            # if it's been set for this experiment, use that
            if self.__class__.flow_rate_override is not None:
                self.flow_rate = self.__class__.flow_rate_override
            # otherwise check user settings
            elif self.method is not None and self.method in appia_settings.flow_rates:
                self.flow_rate = appia_settings.check_flow_rate(self.method)
            # otherwise prompt the user
            else:
                while not isinstance(self._flow_rate, float):
                    try:
                        self.flow_rate = float(input(f'Please enter a flow rate for {self.sample_name} (mL/min): '))
                    except ValueError:
                        logging.error('Flow rate must be a number (e.g., 0.5)')

                if input(f'Set all remaining {self.manufacturer} trace flow rates to {self._flow_rate} for this experiment? (y/n)').lower() == 'y':
                    self.__class__.flow_rate_override = self._flow_rate
                if self.method is not None:
                    if input(f'Save flow rate of {self._flow_rate} for all future traces using method {self.method}? (y/n)').lower() == 'y':
                        appia_settings.update_flow_rates({self.method: self._flow_rate})
                        appia_settings.save_settings()
                        print(f'Saved flow rate: {self.method} = {self._flow_rate}.\nYou can change it later using appia utils.')
            
            return self._flow_rate
        
    @flow_rate.setter
    def flow_rate(self, in_flow_rate:float|None):
        if isinstance(in_flow_rate, float) or in_flow_rate is None:
            self._flow_rate = in_flow_rate
        else:
            raise TypeError
    
    @property
    def df(self) -> pd.DataFrame:
        # put the columns in a standard order
        return self._df[[
            'Time', 'mL', 'Channel',
            'Sample', 'Normalization', 'Value'
        ]]
        
    @df.setter
    def df(self, in_df:pd.DataFrame):
        if not isinstance(in_df, pd.DataFrame):
            raise TypeError
        self._df = in_df
            

class WatersProcessor(HplcProcessor):
    def __init__(self, filename:str, **kwargs):
        super().__init__(filename, **kwargs)
        self.manufacturer = 'Waters'

    @classmethod
    def claim_file(cls, filename) -> bool:
        return filename[-4:] == '.arw'

    def prepare_sample(self) -> None:
        sample_info = pd.read_csv(
            self.filename,
            delim_whitespace = True,
            nrows = 2,
            dtype = str
        )
        self.sample_name = str(sample_info.loc[0]['SampleName'])
        self.channel = re.sub('2475Ch[A-D] ', '', str(sample_info.loc[0]['Channel']))
        self.set_name = str(sample_info.loc[0].get('Sample Set Name'))
        self.method = str(sample_info.loc[0].get('Instrument Method Name'))
        
    def process_file(self) -> None:
        df = pd.read_csv(
            self.filename,
            delim_whitespace = True,
            skiprows = 2,
            names = ["Time", "Signal"],
            header = None,
            dtype = {'Time': np.float32, 'Signal': np.float32}
        )
        df['mL'] = df['Time'] * super().flow_rate
        df['Sample'] = self.sample_name
        df['Channel'] = self.channel
        df = df.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
        df = df.melt(
            id_vars = ['mL', 'Sample', 'Channel', 'Time'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )

        self.df = df

class OldShimProcessor(HplcProcessor):
    def __init__(self, filename, **kwargs):
        self.channel_dict = kwargs.get('channel_dict', {})
        super().__init__(filename, **kwargs)
        self.manufacturer = 'Shimadzu'

    @classmethod
    def claim_file(cls, filename:str) -> bool:
        return filename[-4:] == '.asc'

    def prepare_sample(self) -> None:
        with open(self.filename, 'r') as f:
            lines = [x.rstrip() for x in f]

        line = lines.pop(0)
        while ':' in line:
            line = line.split('\t')

            print(line)
            if line[0] == 'Sample ID:':
                self.sample_name = line[1]
            elif line[0] == 'Method:':
                self.method = line[1].split('\\')[-1]
            elif line[0] == 'Sampling Rate:':
                # final entry in line is the units
                self.sampling_rate = [float(x) for x in line[1:-1]]
            elif line[0] == 'Total Data Points:':
                self.data_points = [int(x) for x in line[1:-1]]

            line = lines.pop(0)

        # the rest of the lines are just signal reads, but we
        # need to add it to the one we've already read into
        # the `line` var.
        self.signal_column = [float(line)]
        self.signal_column.extend([float(x) for x in lines])

    def process_file(self) -> None:
        time_column = []
        for i in range(len(self.data_points)):
            time_column.extend([x * self.sampling_rate[i] for x in range(self.data_points[i])])

        channel_column = []
        for i in range(len(self.data_points)):
            channel_column.extend(['ABCDEFG'[i]] * self.data_points[i])

        df = pd.DataFrame({
            'Time': time_column,
            'Sample': self.sample_name,
            'Channel': channel_column,
            'Signal': self.signal_column
        })
        df['mL'] = df.Time * super().flow_rate
        df = df.replace({'Channel': self.channel_dict})
        df = df.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
        df = df.melt(
            id_vars = ['mL', 'Sample', 'Channel', 'Time'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )

        self.df = df

class NewShimProcessor(HplcProcessor):
    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.manufacturer = 'Shimadzu'

    @classmethod
    def claim_file(cls, filename:str) -> bool:
        if filename[-4:] != '.txt':
            return False
        
        with open(filename, 'r') as f:
            first_line = f.readline().rstrip()

        return first_line == '[Header]'


def new_shim_reader(filename, channel_names = None, flow_rate = None):
    # new shimadzu tables are actually several tables separated by
    # headers, which are in the format `[header]`
    to_append = pd.DataFrame(columns = ['Time', 'Signal', 'Channel', 'Sample', 'mL'])

    with open(filename, 'r') as f:
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
    flow_rate, _ = get_flow_rate(flow_rate, 'Shimadzu Traces', search = False)

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

    for i in range(len(file_list)):

        loading_bar(i+1, (len(file_list)), extension = ' Agilent files')
        filename = file_list[i]

        to_append = pd.read_csv(
            filename,
            sep = '\t',
            names = ['Time', 'Signal'],
            engine = 'python',
            encoding = 'utf_16'
        )

        filename = os.path.split(filename)[1]
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
                    logging.debug(f'Bad channel pattern in file {filename}: {channel}')
                    channel = False
            
            if not channel:
                channel = user_input(f'Please provide a channel name for {filename}:\n')
                if user_input(f'Set channel to "{channel}" for remaining Agilent files? Y/N\n').lower() == 'y':
                    channel_override = channel
        to_append['Channel'] = channel


        # Flow rate
        if not flow_override:
            flow_rate = False
        else:
            flow_rate = flow_override

        if not flow_rate:
            flow_rate, manual_input = get_flow_rate(flow_rate, filename)
            if manual_input and input(f'Set remaining flow rates to {flow_rate}? ').lower() == 'y':
                flow_override = flow_rate
            
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

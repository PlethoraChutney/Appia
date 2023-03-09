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
        self.manufacturer = kwargs.get('manufacturer')
        self.method = kwargs.get('method')
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
            print(f'Self flow rate: {self._flow_rate}')
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
        if in_flow_rate is None:
            self._flow_rate = None
        else:
            self._flow_rate = float(in_flow_rate)
    
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
        super().__init__(
            filename,
            manufacturer = 'Waters',
            **kwargs
        )

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
        super().__init__(
            filename,
            manufacturer = 'Shimadzu',
            **kwargs
        )

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
            elif line[0] == 'Acquisition Date and Time:':
                self.set_name = line[1].split()[0]
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
        super().__init__(
            filename,
            manufacturer = 'Shimadzu',
            **kwargs
        )

    @classmethod
    def claim_file(cls, filename:str) -> bool:
        if filename[-4:] != '.txt':
            return False
        
        with open(filename, 'r') as f:
            first_line = f.readline().rstrip()

        return first_line == '[Header]'
    
    def prepare_sample(self) -> None:
        # parse file into its constituent tables
        with open(self.filename, 'r') as f:
            tables = {}
            curr_table = False
            for line in f:
                table_header_match = re.match(r'\[(.*)\]', line)
                if table_header_match:
                    curr_table = table_header_match.group(1).strip()
                else:
                    if curr_table not in tables:
                        tables[curr_table] = [line]
                    else:
                        tables[curr_table].append(line)

        # get sample name
        for line in tables['Sample Information']:
            if 'Sample Name' in line:
                self.sample_name = line.strip().split('\t')[1]
            elif 'Sample ID' in line:
                try:
                    self.sample_id = line.strip().split('\t')[1]
                except IndexError:
                    self.sample_id = ''
        
        # correct for duplicate sample names
        if self.sample_name != self.sample_id and self.sample_id != '':
            self.sample_name = self.sample_name + "_" + self.sample_id
        else:
            self.sample_name = self.sample_name

        # Get sample set name
        for line in tables['Original Files']:
            if 'Method File' in line:
                method_path = line.strip().split('\t')[1]
                self.method = method_path.split('\\')[-1]
            if 'Batch File' in line:
                batch_path = line.strip().split('\t')[1]
        self.set_name = os.path.split(batch_path)[1][:-4]


        # Get detectors and channels
        for line in tables['Configuration']:
            if 'Detector ID' in line:
                self.detectors = line.strip().split('\t')[1:]
            elif 'Detector Name' in line:
                self.channels = line.strip().split('\t')[1:]

        self.det_to_channel = {}
        for i in range(len(self.detectors)):
            self.det_to_channel[self.detectors[i]] = self.channels[i]

        # Get all chromatograms
        self.chroms = []
        for key in tables:
            if re.match('LC Chromatogram', key):
                self.chroms.append(tables[key])

    def process_file(self) -> None:
        processed_tables = []
        channel_index = -1
        for chrom in self.chroms:
            channel_index += 1
            info_lines = chrom[:15]
            info = {}
            info_patterns = {
                'interval': 'Interval(msec)',
                'num_samples': '# of Points',
                'ex': r'Ex\. Wavelength',
                'em': r'Em\. Wavelength'
            }
            for key in info_patterns:
                for line in info_lines:
                    if re.match(info_patterns[key], line):
                        info[key] = line.strip().split('\t')[1]
                    elif re.match(r'R\.Time', line):
                        skip = info_lines.index(line) + 1
            
            try:
                df = pd.read_csv(
                    StringIO(''.join(chrom)),
                    sep = '\t',
                    skiprows = skip,
                    names = ['Time', 'Signal']
                )
            except NameError:
                # if `skip` is unbound, we should fail to read this file
                logging.error(f'Failed to read {self.filename}')
                return
            
            if 'ex' in info:
                df['Channel'] = f'Ex:{info["ex"]}/Em:{info["em"]}'
            else:
                df['Channel'] = self.channels[channel_index]
            df['Sample'] = self.sample_name
            
            df['mL'] = df['Time'] * self.flow_rate
            processed_tables.append(df)

        df = pd.concat(processed_tables)
        df = df.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
        df = df.melt(
            id_vars = ['mL', 'Sample', 'Channel', 'Time'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )
        self.df = df

class AgilentProcessor(HplcProcessor):
    # Agilent files have basically no metadata,
    # so we need to provide a mechanism similar to our
    # flow-rate solution.
    channel_override = None
    channel_pattern = r'_Channel(.*?)[_.]'
    # tricky one. Gotta use the lookahead so we don't match a
    # dot that's part of the flow.
    flow_pattern = r'_Flow([0-9]*?\.[0-9]*?)?(_|\.(?![0-9]))'

    def __init__(self, filename, **kwargs):
        self._channel = None
        
        flow_match = re.search(
            AgilentProcessor.flow_pattern,
            filename
        )
        if flow_match:
            flow_rate = float(flow_match.group(1))
        else:
            flow_rate = None
        super().__init__(
            filename,
            manufacturer = 'Agilent',
            flow_rate = flow_rate,
            **kwargs
        )


    @classmethod
    def claim_file(cls, filename):
        if filename[-4:] != '.csv':
            return False
        
        with open(filename, 'r') as f:
            line = f.readline().rstrip()

        try:
            # if the first cell is a number, it's an
            # Agilent file. Otherwise it's not. EZPZ.
            _ = float(line.split()[0])
            return True
        except TypeError:
            return False

    @property
    def channel(self) -> str:
        if self._channel is not None:
            return self._channel
        if AgilentProcessor.channel_override is not None:
            return AgilentProcessor.channel_override
        
        # also match a dot in case it's at the end of the file
        channel_match = re.search(AgilentProcessor.channel_pattern, self.filename)
        if channel_match:
            self.channel = channel_match.group(1)
            return self._channel
        
        else:
            self.channel = input(f'Please enter a channel name for {self.filename}: ')
            print('To avoid entering manually in the future, include the channel in the filename like so:')
            print('{filename}_Channel{channel name}_{rest of filename}.csv')

            if input(f'Set channel for all following Agilent files in this experiment to {self._channel}? (y/n) ').lower() == 'y':
                AgilentProcessor.channel_override = self._channel

            return self._channel
        
    @channel.setter
    def channel(self, new_channel:str) -> None:
        self._channel = str(new_channel)

    def prepare_sample(self):
        just_file = os.path.split(self.filename)[1]
        self.sample_name = re.sub(
            AgilentProcessor.channel_pattern,
            # replace with _ for future regex patterns to match
            '_',
            # keep dot in filename in case channel_pattern
            # needs to match it
            just_file[:-3]
        )
        self.sample_name = re.sub(
            AgilentProcessor.flow_pattern,
            '_',
            self.sample_name
        )
        if self.sample_name[-1] in ['.', '_']:
            self.sample_name = self.sample_name[:-1]

    def process_file(self):
        df = pd.read_csv(
            self.filename,
            sep = '\t',
            names = ['Time', 'Signal'],
            engine = 'python',
            encoding='utf-16'
        )
        df['mL'] = df.Time * self.flow_rate
        df['Channel'] = self.channel
        df['Sample'] = self.sample_name

        df = df.groupby(['Sample', 'Channel'], group_keys=False).apply(normalizer)
        df = df.melt(
            id_vars = ['mL', 'Sample', 'Channel', 'Time'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )

        self.df = df

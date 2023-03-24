import pandas as pd
import numpy as np
from io import StringIO
import os
import logging
import re
from appia.processors.core import normalizer
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
        logging.debug(f'HPLC processing arguments for {filename}')
        for argument, value in kwargs.items():
            logging.debug(f'    {argument}: {value}')

        if not hasattr(self.__class__, 'flow_rate_override'):
            # don't want to reset this every time we instantiate
            # a processor, but I also don't want to add it at the
            # beginning of every class definition
            self.__class__.flow_rate_override = None
        self.proc_type = 'hplc'
        self.filename = filename
        self.manufacturer = kwargs.get('manufacturer')
        self.method = kwargs.get('method')
        self.flow_rate = kwargs.get('hplc_flow_rate')
        self.set_name = None
        self.__dict__.update(**kwargs)

        if self.claim_file(filename):
            logging.debug(f'{self.manufacturer} claims {filename}')
            self.claimed = True
            self.prepare_sample()
            self.process_file()
        else:
            self.claimed = False

    @classmethod
    def claim_file(cls, filename):
        pass

    def prepare_sample(self):
        pass

    def process_file(self):
        pass
    
    @property
    def flow_rate(self) -> float:
        logging.debug(f'Flow rate info: self: {self._flow_rate}, override: {self.__class__.flow_rate_override}')
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
    def flow_rate(self, in_flow_rate:float):
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

    @property
    def set_name(self):
        return self._set_name
    
    @set_name.setter
    def set_name(self, new_set_name):
        self._set_name = None if new_set_name is None else new_set_name.replace(os.path.sep, '-')
            

class WatersProcessor(HplcProcessor):
    def __init__(self, filename:str, **kwargs):
        super().__init__(
            filename,
            manufacturer = 'Waters',
            **kwargs
        )

    @classmethod
    def claim_file(cls, filename) -> bool:
        return filename[-4:].lower() == '.arw'

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
        self.channel_dict = kwargs.get('channel_mapping', [])
        super().__init__(
            filename,
            manufacturer = 'Shimadzu',
            **kwargs
        )

    @classmethod
    def claim_file(cls, filename:str) -> bool:
        return filename[-4:].lower() == '.asc'
    
    @property
    def channel_dict(self) -> dict:
        if isinstance(self._channel_dict, list):
            return_dict = {}
            i = 0
            while i < len(self._channel_dict):
                return_dict[self._channel_dict[i]] = self._channel_dict[i + 1]
                i += 2
        
        elif isinstance(self._channel_dict, dict):
            return_dict = self._channel_dict
        else:
            return_dict = {}

        return return_dict
    
    @channel_dict.setter
    def channel_dict(self, new_dict):
        if isinstance(new_dict, dict) or isinstance(new_dict, list):
            self._channel_dict = new_dict
        else:
            raise ValueError

    def prepare_sample(self) -> None:
        with open(self.filename, 'r') as f:
            lines = [x.rstrip() for x in f]

        line = lines.pop(0)
        while ':' in line:
            line = line.split('\t')

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
        logging.debug(self.channel_dict)
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
        if not hasattr(NewShimProcessor, 'prefer_detector'):
            # this attribute is used to pick detectors for channels that have
            # multiple detectors. We want the samples to be consistent across
            # channels, and don't want to have to ask the user multiple times.
            NewShimProcessor.prefer_detector = kwargs.get('prefer_detector')
        super().__init__(
            filename,
            manufacturer = 'Shimadzu',
            **kwargs
        )

    @classmethod
    def claim_file(cls, filename:str) -> bool:
        if filename[-4:].lower() != '.txt':
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

        # Get all chromatograms
        self.chroms = {}
        for key in tables:
            if re.match('LC Chromatogram', key):
                chrom_channel = re.search(
                    r'Chromatogram\((.*?)\)',
                    key
                )
                self.chroms[chrom_channel.group(1)] = tables[key]

        # Get detectors and channels
        # - First, read through the config table to get detector
        # - default channel names.

        for line in tables['Configuration']:
            if 'Detector ID' in line:
                detectors = line.strip().split('\t')[1:]
            elif 'Detector Name' in line:
                channels = line.strip().split('\t')[1:]

        default_det_to_channel = {}
        for i in range(len(detectors)):
            default_det_to_channel[detectors[i]] = channels[i]

        # . Next, read through the data tables to get the
        # . detector channels if they're specified there.
        # . One detector can have multiple channels, so that's
        # . why we have to do this

        detector_channel_pairs = {}
        for detector, table in self.chroms.items():
            excitation = None
            emission = None

            row_number = 0
            line = table[row_number]
            while 'R.Time' not in line:
                if 'Ex.' in line:
                    excitation = line.rstrip().split('\t')[-1]
                if 'Em.' in line:
                    emission = line.rstrip().split('\t')[-1]
                row_number += 1
                line = table[row_number]

            if excitation is not None and emission is not None:
                channel = f'Ex:{excitation}/Em:{emission}'
            else:
                channel = default_det_to_channel[detector]

            detector_channel_pairs[detector] = channel

        # - Now, check if any channels are duplicates of each other
        # - and have the user resolve duplicates if they exist

        if len(set(detector_channel_pairs.values())) != len(detector_channel_pairs.values()):
            counter = {}
            for channel in detector_channel_pairs.values():
                try:
                    counter[channel] += 1
                except KeyError:
                    counter[channel] = 1
            
            duplicate_channels = [x for x in counter.keys() if counter[x] > 1]

            # user selection
            for dup in duplicate_channels:
                duped_detectors = []
                for detector, channel in detector_channel_pairs.items():
                    if channel == dup:
                        duped_detectors.append(detector)

                # check if there is exactly one duplicated detector which matches the user's
                # preferred detector. Otherwise, prompt them for input.
                selected_detector = None
                if NewShimProcessor.prefer_detector is not None:
                    # split on space to avoid "Detector" and add -Ch to avoid "C" matching supriously
                    is_preferred = [x for x in duped_detectors if NewShimProcessor.prefer_detector + '-Ch' in x.split(' ')[1]]
                    if len(is_preferred) == 1:
                        selected_detector = is_preferred[0]
                    elif len(is_preferred) > 1:
                        logging.warning(f'Preferred detector matched more than once: {", ".join(is_preferred)}')
                    else:
                        logging.info(f'Preferred detector {NewShimProcessor.prefer_detector} does not match any duplicated channel.')

                if selected_detector is None:
                    logging.warning('Duplicate channels detected. You can use --prefer-detector to select one in the future.')
                    print(f'Select a detector for {dup}. Any non-numeric choice will default to 0.')
                    for i in range(len(duped_detectors)):
                        print(f'{i}: {re.sub("-Ch[0-9]*", "", duped_detectors[i])}')
                    
                    try:
                        selected_detector = duped_detectors[int(input())]
                        # update the class preferred detector so that the user isn't prompted for each file.
                        NewShimProcessor.prefer_detector = re.search(r'Detector (.*?)-Ch[0-9]*', selected_detector).group(1)
                    except (ValueError, IndexError):
                        selected_detector = duped_detectors[0]

                # drop other detectors for this channel from the paired dict
                to_drop = []
                for detector, channel in detector_channel_pairs.items():
                    if channel == dup and detector != selected_detector:
                        to_drop.append(detector)

                for detector in to_drop:
                    del detector_channel_pairs[detector]
        
        self.channels = detector_channel_pairs

    def process_file(self) -> None:
        processed_tables = []
        for detector, chrom in self.chroms.items():
            # if the detector isn't in channels, that means
            # the user selected a different detector for the
            # given channel
            if detector not in self.channels:
                continue
            info_lines = chrom[:15]
            info = {}
            info_patterns = {
                'interval': 'Interval(msec)',
                'num_samples': '# of Points'
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
            
            df['Channel'] = self.channels[detector]
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
        self._channel = kwargs.get('agilent_channel_name')
        flow_rate = kwargs.get('hplc_flow_rate')
        mod_args = kwargs.copy()
        
        flow_match = re.search(
            AgilentProcessor.flow_pattern,
            filename
        )
        if flow_match:
            if flow_rate is not None:
                logging.warning('Agilent filename has a flow rate, but a flow rate was also passed as an argument. Using the argument flow rate. To use the filename flowrate, do not use --hplc-flow-rate option.')
            else:
                mod_args['hplc_flow_rate'] = float(flow_match.group(1))
        super().__init__(
            filename,
            manufacturer = 'Agilent',
            **mod_args
        )


    @classmethod
    def claim_file(cls, filename):
        if filename[-4:].lower() != '.csv':
            return False
        
        with open(filename, 'r', encoding='utf-16') as f:
            line = f.readline().rstrip()

        try:
            # if the first cell is a number, it's an
            # Agilent file. Otherwise it's not. EZPZ.
            _ = float(line.split()[0])
            return True
        except ValueError:
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

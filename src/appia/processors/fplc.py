import pandas as pd
import os
import logging
from appia.parsers.user_settings import appia_settings
from appia.processors.core import normalizer

class FplcProcessor(object):
    """
    The parent processor for all Appia FPLC processing. Any
    FPLC processors should inherit from this class.
    """
    def __init__(self, filename, **kwargs):
        if not hasattr(self.__class__, 'column_volume_override'):
            self.__class__.column_volume_override = None
        self._df = None
        self.proc_type = 'fplc'
        self.filename = filename
        self.set_name = kwargs.get('set_name')
        self.manufacturer = kwargs.get('manufacturer')
        self._column_volume = kwargs.get('fplc_cv')
        self.__dict__.update(**kwargs)

        if self.claim_file(filename):
            logging.debug(f'{self.manufacturer} claims {filename}')
            self.claimed = True
            self.prepare_sample()
            self.process_file()
        else:
            self.claimed = False

    @property
    def column_volume(self):
        if self._column_volume is not None:
            return self._column_volume
        elif self.__class__.column_volume_override is not None:
            return self.column_volume_override
        elif appia_settings.default_column_volume is not None:
            return appia_settings.default_column_volume
        else:
            return self.prompt_column_volume()
        
    def prompt_column_volume(self):
        cv = None
        while not isinstance(cv, float):
            try:
                cv = float(input('Please input FPLC column volume (mL): '))
            except ValueError:
                print('CV must be a number')
        
        if input(f'Set remaining FPLC CVs to {cv}? (y/n) ').lower() == 'y':
            self.__class__.column_volume_override = cv
        
        if input(f'Set {cv} as your default FPLC CV? (y/n) ').lower() == 'y':
            appia_settings.default_column_volume = cv
            appia_settings.save_settings()
            print('You can change this in the future using appia utils.')

        return cv


    @classmethod
    def claim_file(cls, filename):
        pass

    def prepare_sample(self):
        pass

    def process_file(self):
        pass

    @property
    def df(self) -> pd.DataFrame:
        return self._df[[
            'mL', 'CV', 'Channel', 'Fraction',
            'Sample', 'Normalization', 'Value'
        ]]
    
    @df.setter
    def df(self, in_df):
        if not isinstance(in_df, pd.DataFrame):
            raise TypeError
        self._df = in_df


class AktaProcessor(FplcProcessor):
    def __init__(self, filename, **kwargs):
        super().__init__(
            filename,
            manufacturer = 'AKTA',
            **kwargs
        )
    
    @classmethod
    def claim_file(cls, filename) -> bool:
        if filename[-4:].lower() != '.csv':
            return False
        
        try:
            with open(filename, 'r', encoding='utf-16') as f:
                line = f.readline().rstrip()
        except UnicodeDecodeError:
            return False
        
        if line.split()[0] == 'Chrom.1':
            return True
        else:
            return False
        
    def prepare_sample(self):
        return super().prepare_sample()
        
    def process_file(self):
        try:
            fplc_trace = pd.read_csv(
                self.filename, skiprows = 1,
                header = [1],
                encoding = 'utf-16-le',
                delimiter = '\t',
                engine = 'python'
            )
        except UnicodeDecodeError:
            fplc_trace = pd.read_csv(
                self.filename, skiprows = 1,
                header = [1],
                encoding = 'utf-8',
                delimiter = ',',
                engine = 'python'
            )

        # The AKTA exports data with several different ml columns, each with their
        # own name (like ml.2, ml.3, etc.). These are mL axes for each channel.
        # Unfortunately, they are different for each channel! So we need to keep
        # each and know which channel it goes with. Additionally, since users
        # don't have to export every channel every time, we can't hard code positions
        
        fplc_trace = fplc_trace.filter(regex = r'(ml|mAU$|mS/cm$|%$|Fraction)')
        columns = fplc_trace.columns
        renaming = {}
        for col_name in ['mAU', 'mS/cm', '%', 'Fraction']:
            if col_name in columns:
                column = columns.get_loc(col_name)
                renaming[columns[column-1]] = f'mL_{col_name}'

        fplc_trace = fplc_trace.rename(columns = renaming)

        channels = []
        for column in ['mAU', 'mS/cm', '%']:
            channel = pd.melt(
                fplc_trace,
                id_vars = [f'mL_{column}'],
                value_vars = [column],
                var_name = 'Channel',
                value_name = 'Signal')
            channel = channel.rename(columns = {f'mL_{column}':'mL'}).dropna()
            channels.append(channel)
        df = pd.concat(channels, ignore_index=True)

        df['Fraction'] = 1
        frac_mL = fplc_trace['mL_Fraction'].dropna()
        for i in range(len(frac_mL)):
            # The +2 here is a magic number. For whatever reason, the fractions
            # generated by this method were off by two from those displayed in
            # the AKTA software. And since those are where your protein actually
            # ends up, it's pretty important that everything matches.
            df.loc[df['mL'] > frac_mL[i], 'Fraction'] = i + 2

        df['CV'] = df['mL'] / self.column_volume

        df['Sample'] = os.path.split(self.filename)[1][:-4]
        # filter out washes
        df = df.loc[(df.CV >= 0) & (df.CV <=1)]

        df = df.groupby(['Channel', 'Sample'], group_keys=False).apply(normalizer)
        df = df.melt(
            id_vars = ['mL', 'CV', 'Channel', 'Fraction', 'Sample'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )

        self.df = df


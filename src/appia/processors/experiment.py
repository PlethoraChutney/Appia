import pandas as pd
import os
from appia.processors.core import normalizer
from math import ceil

class Experiment:
    def __init__(self, id) -> None:
        self.id = id
        self.version = 4
        self._hplc = None
        self._fplc = None

    @property
    def hplc(self):
        try:
            return self._hplc
        except AttributeError:
            return None

    @hplc.setter
    def hplc(self, df):
        if isinstance(df, pd.DataFrame) or df is None:
            try:
                self._hplc = df.sort_values(
                    by = ['Normalization', 'Channel', 'mL']
                )
            except AttributeError:
                self._hplc = df
        else:
            raise TypeError('HPLC input is not a pandas dataframe')

    @property
    def fplc(self):
        try:
            return self._fplc
        except AttributeError:
            return None

    @fplc.setter
    def fplc(self, df):
        if isinstance(df, pd.DataFrame) or df is None:
            self._fplc = df
        else:
            raise TypeError('FPLC input is not a pandas dataframe')

    @property
    def wide(self):
        wide = self.hplc.copy()
        wide = wide.loc[wide['Normalization'] == 'Signal']
        wide['Sample'] = wide['Sample'].astype(str) + ' ' + wide['Channel']
        wide.drop(['Channel', 'Normalization'], axis = 1)
        wide = wide.pivot_table(
            index = 'Time',
            columns = 'Sample',
            values = 'Value'
        )
        return wide

    def __repr__(self):
        to_return = f'Experiment "{self.id}" with '
        if self.hplc is not None:
            to_return += 'HPLC '
        if self.hplc is not None and self.fplc is not None:
            to_return += 'and '
        if self.fplc is not None:
            to_return += 'FPLC '
        if self.hplc is None and self.fplc is None:
            to_return += 'no '
        to_return += 'data'

        return to_return

    def extend_hplc(self, hplc):
        if not isinstance(hplc, pd.DataFrame):
            raise TypeError(f'Tried to extend experiment hplc with {type(hplc)}')

        self.hplc = pd.concat([self.hplc, hplc])

    def show_tables(self):
        print('HPLC:')
        print(self.hplc)
        print('FPLC:')
        print(self.fplc)

    def jsonify(self):
        if self.hplc is not None:
            hplc_json = self.hplc.pivot_table(
                    index = ['mL', 'Channel', 'Time', 'Normalization'],
                    columns = 'Sample',
                    values = 'Value'
                ).reset_index().to_json()
        else:
            hplc_json = ''

        if self.fplc is not None:
            fplc_json = self.fplc.to_json()
        else:
            fplc_json = ''

        doc = {
            '_id': self.id,
            'version': self.version,
            'hplc': hplc_json,
            'fplc': fplc_json
        }

        return doc

    def renormalize_hplc(self, norm_range, strict):
        if self.hplc is None:
            raise ValueError('No HPLC data')

        # this arcane string of pandas commands is the equivalent of pivot_wider from tidyverse
        # from https://medium.com/@durgaswaroop/reshaping-pandas-dataframes-melt-and-unmelt-9f57518c7738;.'/
        hplc = self.hplc.pivot(
                index = ['mL', 'Sample', 'Channel', 'Time'],
                columns = ['Normalization']
            )['Value'].reset_index()
        hplc = hplc.groupby(['Sample', 'Channel'], group_keys=False).apply(lambda x: normalizer(x, norm_range, strict))
        hplc = hplc.melt(
            id_vars = ['mL', 'Sample', 'Channel', 'Time'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )
        self.hplc = hplc

    def renormalize_fplc(self, norm_range, strict):
        if self.fplc is None:
            raise ValueError('No FPLC data')

        fplc = self.fplc.pivot(
                index = ['mL', 'CV', 'Fraction', 'Channel', 'Sample'],
                columns = ['Normalization']
            )['Value'].reset_index()
        fplc = fplc.groupby(['Sample', 'Channel'], group_keys=False).apply(lambda x: normalizer(x, norm_range, strict))
        fplc = fplc.melt(
            id_vars = ['mL', 'CV', 'Channel', 'Fraction', 'Sample'],
            value_vars = ['Signal', 'Normalized'],
            var_name = 'Normalization',
            value_name = 'Value'
        )
        self.fplc = fplc

    def reduce_hplc(self, num_points):
        # reduce the number of points in the hplc trace to num_points per sample/channel/norm

        def reduction_factor(df, final_points):
            reduction_factor = ceil(df.shape[0]/final_points)
            return df[::reduction_factor]
        try:
            self.hplc = self.hplc.groupby(
                ['Channel', 'Sample', 'Normalization'],
                group_keys=False,
                as_index = False
                ).apply(
                    lambda x: reduction_factor(x, num_points)
                )
            self.hplc = self.hplc.reset_index(drop = True)
        except AttributeError:
            return

    def rename_channels(self, channel_name_dict):
        self.hplc = self.hplc.replace({'Channel': channel_name_dict})

    def hplc_csv(self, outfile):
        if outfile[-4:] == '.csv':
            outfile = outfile[:-4]
        if self.hplc is not None:
            self.hplc.to_csv(outfile + '-long.csv', index = False)
            self.wide.to_csv(outfile + '-wide.csv', index = True)

            return outfile + '-long.csv'

    def fplc_csv(self, outfile):
        if outfile[-4:] != '.csv':
            outfile = outfile + '.csv'
        
        if self.fplc is not None:
            self.fplc.to_csv(outfile, index = False)
            return outfile

    def save_csvs(self, path):
        hplc_csv = self.hplc_csv(os.path.join(path, f'{self.id}_hplc'))
        fplc_csv = self.fplc_csv(os.path.join(path, f'{self.id}_fplc'))

        return hplc_csv, fplc_csv


def concat_experiments(exp_list):
        hplcs = []
        fplcs = []

        for exp in [x for x in exp_list if x.hplc is not None]:
            hplc = exp.hplc
            hplc['Sample'] = f'{exp.id}: ' + hplc['Sample'].astype(str)
            hplcs.append(hplc)

        for exp in [x for x in exp_list if x.fplc is not None]:
            fplc = exp.fplc
            fplc['Sample'] = exp.id
            fplcs.append(fplc)

        concat_exp = Experiment('concat')
        try:
            concat_exp.hplc = pd.concat(hplcs)
        except ValueError:
            pass

        try:
            concat_exp.fplc = pd.concat(fplcs)
        except ValueError:
            pass
        
        return concat_exp
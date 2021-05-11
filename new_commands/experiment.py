import pandas as pd
from database import pull_experiment

class Experiment:
    def __init__(self, id):
        self.id = id
        self.version = 3
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
        if self.hplc:
            raise ValueError(f'Experiment {self.id} already has an HPLC')
        elif isinstance(df, pd.DataFrame):
            self._hplc = df
        else:
            raise TypeError('HPLC input is not a pandas dataframe')

    @property
    def fplc(self):
        try:
            return self._fplc
        except AttributeError:
            return none

    @fplc.setter
    def fplc(self, df):
        if self.fplc:
            raise ValueError(f'Experiment {self.id} already has an FPLC')
        elif isinstance(df, pd.DataFrame):
            self._fplc = df
        else:
            raise TypeError('FPLC input is not a pandas dataframe')

    def __repr__(self):
        to_return = f'Experiment "{self.id}", version {self.version}, with '
        if self.hplc is not None:
            to_return += 'HPLC '
        if self.hplc is not None and self.fplc is not None:
            to_return += 'and '
        if self.fplc is not None:
            to_return += 'FPLC '
        if self.hplc is None and self.fplc is None:
            to_return += 'no '
        to_return += 'data.'

        return to_return

    def show_tables(self):
        print('HPLC:')
        print(self.hplc)
        print('FPLC:')
        print(self.fplc)

    def jsonify(self):
        if self.hplc is not None:
            hplc_json = self.hplc.to_json()
        else:
            hplc_json = ''

        if self.fplc is not None:
            fplc_json = self.fplc.to_json()
        else:
            fplc_json = ''

        doc = {
            '_id': self.id,
            'version': self.version,
            'hplc': h_json,
            'fplc': f_json
        }

        return doc


exp = Experiment('test')
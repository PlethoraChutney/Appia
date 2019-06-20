import numpy as np
import pandas as pd
import sys
import os
import couchdb

def init_db():
    user = 'admin'
    password = 'my_secret_password'
    couchserver = couchdb.Server(f'http://{user}:{password}@127.0.0.1:5984')

    dbname = 'traces'
    if dbname in couchserver:
        db = couchserver[dbname]
    else:
        db = couchserver.create(dbname)

    return(db)

class Experiment:
    def __init__(self, input):
        if type(input) == couchdb.client.Document:
            self.id = input['_id']
            self.time = input['time']
            self.signal = input['signal']
            self.channel = input['channel']
            self.sample = input['sample']
        elif os.path.isdir(input):
            self.id = os.path.split(input)[-1]
            in_df = pd.read_csv(os.path.join(input, 'long_chromatograms.csv'))
            self.normalized = in_df.groupby(['Sample', 'Channel']).transform(lambda x: ((x - x.min()) / (x.max() - x.min())))['Signal']
            self.time = in_df['Time'].tolist()
            self.signal = in_df['Signal'].tolist()
            self.channel = in_df['Channel'].tolist()
            self.sample = in_df['Sample'].tolist()
        else:
            print('Input not recognized')

    def as_pandas_df(self):
        out_df = pd.DataFrame(
            {
                'Time': self.time,
                'Signal': self.signal,
                'Normalized': self.normalized,
                'Channel': self.channel,
                'Sample': self.sample
            }
        )

        return(out_df)

    def __store_in_db(self, db):
        doc = {
            '_id': self.id,
            'time': self.time,
            'signal': self.signal,
            'channel': self.channel,
            'sample': self.sample
        }
        db.save(doc)

    def add_to_db(self, db):
        if db.get(self.id) is None:
            self.__store_in_db(db)

    def get_plotly(self):
        df = self.as_pandas_df()
        graphs = {}
        for channel in df['Channel'].unique():
            data = []
            df_channel = df[df.Channel == channel]
            for level in df_channel['Sample'].unique():
                df_level = df_channel[df_channel.Sample == level]
                trace = {'x': df_level['Time'], 'y': df_level['Signal'], 'name': level, 'type': 'scatter'}
                data.append(trace)
            graphs[channel] = data
        for channel in df['Channel'].unique():
            data = []
            df_channel = df[df.Channel == channel]
            for level in df_channel['Sample'].unique():
                df_level = df_channel[df_channel.Sample == level]
                trace = {'x': df_level['Time'], 'y': df_level['Normalized'], 'name': level, 'type': 'scatter'}
                data.append(trace)
            graphs[f'Normalized {channel}'] = data
        return(graphs)

    def __repr__(self):
        self.as_pandas_df()

def collect_experiments(directory, db):
    list_of_dirs = []
    list_of_experiments = []
    for sub_dir in os.listdir(directory):
        if os.path.isfile(os.path.join(directory, sub_dir, 'long_chromatograms.csv')):
            list_of_dirs.append(os.path.abspath(os.path.join(directory, sub_dir)))
    for experiment in list_of_dirs:
        list_of_experiments.append(Experiment(experiment))

    for experiment in list_of_experiments:
        experiment.add_to_db(db)

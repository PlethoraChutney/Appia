import numpy as np
import pandas as pd
import sys
import os
import couchdb
import dash
import logging
import dash_core_components as dcc
import dash_html_components as html
from subcommands.config import config

# 1 Database initialization ----------------------------------------------------

# make a config.py with your couchdb username and password in it. Don't put them here!
def init_db(config):
    user = config['user']
    password = config['password']
    host = config['host']
    couchserver = couchdb.Server(f'http://{user}:{password}@{host}:5984')

    dbname = 'traces'
    if dbname in couchserver:
        db = couchserver[dbname]
    else:
        db = couchserver.create(dbname)

    return(db)

# 2 Experiment class -----------------------------------------------------------
# * 2.1 Experiment I/O ---------------------------------------------------------
class Experiment:
    def __init__(self, input, reduce = 1):
        if type(input) == couchdb.client.Document:
            self.exptype = 'hplc'
            self.id = input['_id']
            self.time = input['time']
            self.signal = input['signal']
            self.normalized = input['normalized']
            self.channel = input['channel']
            self.sample = input['sample']
        # Lists are given to Experiment() when we're merging several datasets
        elif type(input) == list:
            self.exptype = 'hplc'
            list_of_dfs = [x.as_pandas_df() for x in input]
            merged_df = pd.concat(list_of_dfs)
            self.time = merged_df['Time'].tolist()
            self.signal = merged_df['Signal'].tolist()
            self.channel = merged_df['Channel'].tolist()
            self.sample = merged_df['Sample'].tolist()
            self.normalized = merged_df['Normalized'].tolist()

        # dataframes come from combined processing
        elif isinstance(input, pd.DataFrame):
            if reduce != 1:
                # extremely large datasets, like large-scale expressions, typically
                # do not need the quarter-second or half-second resolution afforded
                # by the HPLC. We can decimate these datasets to make them load
                # faster in the web interface and other programs.
                in_df = in_df.iloc[::reduce]

            self.exptype = 'combined'
            self.expname = input['Experiment'].tolist()
            self.volume = input['mL'].tolist()
            self.cv = input['Column Volume'].tolist()
            self.sample = input['Sample'].tolist()
            self.channel = input['Channel'].tolist()
            self.signal = input['Signal'].tolist()

        # Directories are given to Experiment() when we're first adding csv files
        # to the couchdb database
        elif os.path.isdir(input):
            self.exptype = 'hplc'
            self.id = os.path.split(input)[-1].replace('_processed', '')
            in_df = pd.read_csv(os.path.join(input, 'long_chromatograms.csv'))
            in_df['Normalized'] = in_df.groupby(['Sample', 'Channel']).transform(lambda x: ((x - x.min()) / (x.max() - x.min())))['Signal'].tolist()
            in_df.fillna(0, inplace = True)

            if reduce != 1:
                in_df = in_df.iloc[::reduce]

            self.time = in_df['Time'].tolist()
            self.signal = in_df['Signal'].tolist()
            self.channel = in_df['Channel'].tolist()
            self.sample = in_df['Sample'].tolist()
            self.normalized = in_df['Normalized'].tolist()
        else:
            raise TypeError('Input is not a couchdb or csv')

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
            'normalized': self.normalized,
            'channel': self.channel,
            'sample': self.sample
        }
        db.save(doc)

    def add_to_db(self, db):
        try:
            self.__store_in_db(db)
        except:
            logging.error('Experiment already in database! Rerun this script with --rename to add it to the database.')

# * 2.2 Experiment graph production --------------------------------------------

    def get_plotly(self):
        df = self.as_pandas_df()
        graphs = {}
        plotly_graphs = []
        # Plotly graphs are built trace by trace, unlike R, where you specify
        # a set of data over which to break lines (i.e., you say "Color by sample"
        # in R but you build each sample line individually in python). So we need
        # to loop over channels, and we need to loop over normalzied or raw data.
        # That's what these two set of nested for loops do.
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
        # Return html elements, not raw plotly graphs
        for channel in graphs.keys():
            plotly_graphs.append(dcc.Graph(
                style={'height': 600},
                id=f'channel-{channel}',
                figure={
                    'data': graphs[channel],
                    'layout': {'title': f'{channel}'}
                }
            ))

        return(plotly_graphs)

    def __repr__(self):
        self.as_pandas_df()

# 3 Misc db functions ----------------------------------------------------------

def collect_experiments(directory, db, reduce = 1):
    list_of_dirs = []
    list_of_experiments = []

    for sub_dir in [os.path.abspath(x[0]) for x in os.walk(directory) if x != directory]:
        if os.path.isfile(os.path.join(sub_dir, 'long_chromatograms.csv')):
            list_of_dirs.append(os.path.abspath(os.path.join(directory, sub_dir)))

    for experiment in list_of_dirs:
        list_of_experiments.append(Experiment(experiment, reduce))

    for experiment in list_of_experiments:
        logging.info(f'Adding experiment {experiment.id}')
        experiment.add_to_db(db)

def update_experiment_list(db):
    list_of_experiments = []
    for docid in db.view('_all_docs'):
        list_of_experiments.append(docid['id'])
    return list_of_experiments

def remove_experiment(db, exp_id):
    try:
        db.delete(db[exp_id])
    except:
        logging.error(f'Could not find experiment {exp_id}')

import numpy as np
import pandas as pd
import sys
import os
import couchdb
import dash
import logging
import argparse
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
class Experiment:
    def __init__(self, id, hplc, fplc, reduce = 1):
        self.id = id
        self.hplc = hplc.iloc[::reduce]
        self.hplc.reset_index(inplace = True, drop = True)

        if fplc is not None:
            self.combined = True
            self.fplc = fplc.iloc[::reduce]
            self.fplc.reset_index(inplace = True, drop = True)
        else:
            self.combined = False
    def __repr__(self):
        if self.combined:
            data_types = 'HPLC and FPLC data.'
        else:
            data_types = 'HPLC data only.'
        return f'Experiment "{self.id}" with {data_types}'

    def show_tables(self):
        print(self.hplc)
        if self.combined:
            print(self.fplc)

    def upload_to_couchdb(self, db):
        try:
            h_json = self.hplc.to_json()
            if self.combined:
                f_json = self.fplc.to_json()
            else:
                f_json = ''

            doc = {
                '_id': self.id,
                'hplc': h_json,
                'fplc': f_json,
            }

            db.save(doc)
        except couchdb.http.ResourceConflict:
            logging.error(f'Experiment "{self.id}" already in database.')

# * 2.2 Experiment graph production --------------------------------------------

    def get_plotly(self):
        if self.combined:
            pass
        else:
            return self.get_hplc()

    def get_hplc(self):
        hplc = self.hplc
        hplc['Normalized'] = hplc.groupby(['Sample', 'Channel']).transform(lambda x: ((x - x.min()) / (x.max() - x.min())))['Signal'].tolist()
        hplc.fillna(0, inplace = True)

        graphs = {}
        plotly_graphs = []
        # Plotly graphs are built trace by trace, unlike R, where you specify
        # a set of data over which to break lines (i.e., you say "Color by sample"
        # in R but you build each sample line individually in python). So we need
        # to loop over channels, and we need to loop over normalzied or raw data.
        # That's what these two set of nested for loops do.
        for channel in hplc['Channel'].unique():
            data = []
            hplc_channel = hplc[hplc.Channel == channel]
            for level in hplc_channel['Sample'].unique():
                hplc_level = hplc_channel[hplc_channel.Sample == level]
                trace = {'x': hplc_level['mL'], 'y': hplc_level['Signal'], 'name': level, 'type': 'scatter'}
                data.append(trace)
            graphs[channel] = data
        for channel in hplc['Channel'].unique():
            data = []
            hplc_channel = hplc[hplc.Channel == channel]
            for level in hplc_channel['Sample'].unique():
                hplc_level = hplc_channel[hplc_channel.Sample == level]
                trace = {'x': hplc_level['mL'], 'y': hplc_level['Normalized'], 'name': level, 'type': 'scatter'}
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

        return plotly_graphs

    def get_fplc(self):
        fplc = self.fplc



#3 Misc db functions -----------------------------------------------------------

def pull_experiment(db, id):
    doc = db.get(id)
    hplc = pd.read_json(doc['hplc'])
    try:
        fplc = pd.read_json(doc['fplc'])
    except ValueError:
        fplc = None

    return Experiment(
        id = doc['_id'],
        hplc = hplc,
        fplc = fplc,
        reduce = 1
    )

def collect_hplc(directory, db, reduce = 1):
    list_of_dirs = []
    list_of_experiments = []

    for sub_dir in [os.path.abspath(x[0]) for x in os.walk(directory) if x != directory]:
        if os.path.isfile(os.path.join(sub_dir, 'long_chromatograms.csv')):
            list_of_dirs.append(os.path.abspath(os.path.join(directory, sub_dir)))

    for hplc_dir in list_of_dirs:
        id = os.path.split(hplc_dir)[-1].replace('_processed', '')
        hplc = pd.read_csv(os.path.join(hplc_dir, 'long_chromatograms.csv'))
        list_of_experiments.append(Experiment(id, hplc, None, reduce))

    for experiment in list_of_experiments:
        logging.info(f'Adding experiment {experiment.id}')
        experiment.upload_to_couchdb(db)

def update_experiment_list(db):
    list_of_experiments = []
    for docid in db.view('_all_docs'):
        list_of_experiments.append(docid['id'])
    return list_of_experiments

def remove_experiment(db, exp_id):
    try:
        db.delete(db[exp_id])
    except couchdb.http.ResourceNotFound:
        logging.error(f'Could not find experiment {exp_id}')

def three_column_print(in_list):
    in_list = iter(in_list)
    for i in in_list:
        print('{:<45}{:<45}{}'.format(i, next(in_list, ""), next(in_list, '')))

def main(args):
    db = init_db(config)

    if args.list:
        three_column_print(update_experiment_list(db))

    if args.delete:
        for exp in args.delete:
            remove_experiment(db, exp)

    if args.mass_add:
        collect_hplc(args.mass_add, db)

parser = argparse.ArgumentParser(
    description = 'Database management',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    '-l', '--list',
    help = 'Print list of all experiments in database',
    action = 'store_true'
)
parser.add_argument(
    '-d', '--delete',
    help = 'Delete experiment(s) by name',
    type = str,
    nargs = '+'
)
parser.add_argument(
    '--mass-add',
    help = 'Add multiple experiments or multiple directories of experiments',
    type = str,
    nargs = '+'
)

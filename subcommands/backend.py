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
import plotly.express as px
import plotly.graph_objects as go
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
        self.version = 1
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
        return f'Experiment "{self.id}", version {self.version}, with {data_types}'

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
                'version': self.version,
                'hplc': h_json,
                'fplc': f_json,
            }

            db.save(doc)
        except couchdb.http.ResourceConflict:
            logging.error(f'Experiment "{self.id}" already in database.')
            if input(f'Overwrite database copy of {self.id}? Y/N\n').lower() == 'y':
                logging.info('Uploading new version')
                remove_experiment(db, self.id)
                self.upload_to_couchdb(db)
            else:
                logging.info('Skipping database upload.')

# * 2.2 Experiment graph production --------------------------------------------

    def get_plotly(self):
        if self.combined:
            combined_graphs = {}

            fplc = self.fplc

            # if you don't create a bunch of seperate GO objects, the fill is
            # screwy
            #
            # plotly express would work, but if you turn off a middle fraction
            # the fill also gets weird
            fplc_graph = go.Figure()
            for frac in set(fplc['Fraction']):
                fplc_graph.add_trace(
                    go.Scatter(
                        x = fplc[fplc.Fraction == frac]['mL'],
                        y = fplc[fplc.Fraction == frac]['Signal'],
                        mode = 'lines',
                        fill = 'tozeroy',
                        visible = 'legendonly'
                    )
                )
            fplc_graph.add_trace(
                go.Scatter(
                    x = fplc['mL'],
                    y = fplc['Signal'],
                    mode = 'lines',
                    showlegend = False,
                    line = {'color': 'black'}
                )
            )
            fplc_graph.update_layout(template = 'plotly_white')
            combined_graphs['FPLC'] = fplc_graph

            hplc_graphs = self.get_hplc()[1]
            for data_type in ['Signal', 'Normalized']:
                combined_graphs[data_type] = hplc_graphs[data_type]

            html_graphs = []
            for data_type in combined_graphs.keys():
                html_graphs.extend([
                    html.H5(
                        children = data_type,
                        style = {'textAlign': 'center'}
                    ),
                    dcc.Graph(
                        style={'height': 600},
                        id=f'data-{data_type}',
                        figure=combined_graphs[data_type]
                    )
                ])
            return html_graphs

        else:
            return self.get_hplc()[0]

    def get_hplc(self):
        hplc = self.hplc.sort_values(['Sample', 'mL'], ascending = [True, True])

        raw_graphs = {}
        html_graphs = []
        for data_type in ['Signal', 'Normalized']:
            fig = px.line(
                data_frame = hplc,
                x = 'mL',
                y = data_type,
                color = 'Sample',
                facet_row = 'Channel',
                template = 'plotly_white'
            )
            fig.layout.yaxis2.update(matches = None)
            raw_graphs[data_type] = fig

        for data_type in raw_graphs.keys():
            html_graphs.extend([
                html.H5(
                    children = data_type,
                    style = {'textAlign': 'center'}
                ),
                dcc.Graph(
                    style={'height': 600},
                    id=f'data-{data_type}',
                    figure=raw_graphs[data_type]
                )
            ])

        return (html_graphs, raw_graphs)




#3 Misc db functions -----------------------------------------------------------

def pull_experiment(db, id):
    doc = db.get(id)
    hplc = pd.read_json(doc['hplc'])
    try:
        fplc = pd.read_json(doc['fplc'])
    except ValueError:
        fplc = None

    if doc['version'] == 1:
        return Experiment(
            id = doc['_id'],
            hplc = hplc,
            fplc = fplc,
            reduce = 1
        )

def concat_experiments(exp_list):
    hplcs = []

    for exp in exp_list:
        hplc = exp.hplc
        hplc['Sample'] = f'{exp.id}: ' + hplc['Sample'].astype(str)
        hplcs.append(hplc)

    hplcs = pd.concat(hplcs)
    concat_exp = Experiment('Combined', hplcs, None)

    return concat_exp

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

def update_db(db):
    if input('Did you back up your couchDB before running this option? Type "I backed up my database".\n').lower() != 'i backed up my database':
        logging.error('Back up your database before upgrading.')
        return

    exp_list = update_experiment_list(db)
    upgraded_experiments = []
    for name in exp_list:
        e = db.get(name)
        try:

            logging.info(f'Skipping modern experiment {e.id} (version {e.version})')
        # old experiments didn't have a version number
        except AttributeError:
            logging.warning('Guessing flow rate based on total run time.')
            if max(e['time']) < 20:
                flow_rate = 0.3
            else:
                flow_rate = 0.5

            hplc = pd.DataFrame(
                {
                    'Time': e['time'],
                    'Signal': e['signal'],
                    'Channel': e['channel'],
                    'Sample': e['sample']
                }
            )

            hplc = hplc.astype({
                'Time': np.float64,
                'Signal': np.float64,
                'Channel': str,
                'Sample': str
            })
            hplc['mL'] = hplc['Time'] * flow_rate
            hplc['Normalized'] = hplc.groupby(['Sample', 'Channel']).transform(lambda x: ((x - x.min()) / (x[hplc.Time > 0.51].max() - x.min())))['Signal'].tolist()

            new_exp = Experiment(e.id, hplc, None)

            logging.debug(f'{e.id} becomes {new_exp}')

            upgraded_experiments.append(new_exp)

    logging.info(f'Uploading {upgraded_experiments}')

    for exp in upgraded_experiments:
        remove_experiment(db, exp.id)
        exp.upload_to_couchdb(db)


def main(args):
    db = init_db(config)

    if args.list:
        three_column_print(update_experiment_list(db))

    if args.delete:
        for exp in args.delete:
            remove_experiment(db, exp)

    if args.mass_add:
        collect_hplc(args.mass_add, db)

    if args.upgrade:
        update_db(db)

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

parser.add_argument(
    '--upgrade',
    help = 'Download all experiments in the couchdb and upgrade them to modern, combined experiments. This is destructive! Backup first!',
    action = 'store_true'
)

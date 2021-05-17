import couchdb
import logging
import pandas as pd
from .experiment import Experiment
from .core import three_column_print
import json

class Config:
    def __init__(self, config_file) -> None:
        with open(config_file) as conf:
            config = json.load(conf)

        self.cuser = config['user']
        self.cpass = config['password']
        self.chost = config['host']
        self.slack_token = config['token']
        self.slack_channel = config['chromatography_channel']

    def __repr__(self) -> str:
        return f'config object for host {self.chost}'

class Database:
    def __init__(self, config) -> None:
        self.config = config
        self.version = 3
        couchserver = couchdb.Server(f'http://{config.cuser}:{config.cpass}@{config.chost}:5984')

        dbname = 'traces'
        if dbname in couchserver:
            self.db = couchserver[dbname]
        else:
            self.db = couchserver.create(dbname)

    def __repr__(self) -> str:
        return f'CouchDB at {self.config.chost}'

    def update_experiment_list(self):
        return [x['id'] for x in self.db.view('_all_docs')]


    def pull_experiment(self, id):
        doc = self.db.get(id)
        new_exp = Experiment(id)

        try:
            new_exp.hplc = pd.read_json(doc['hplc'])
        except ValueError:
            pass

        try:
            new_exp.fplc = pd.read_json(doc['fplc'])
        except ValueError:
            pass

        try:
            if doc['version'] == 2:
                logging.info('Upgrading from Experiment v2')
            elif doc['version'] != self.version:
                logging.error('Out of date experiment. Perform db migration.')
        except KeyError:
            logging.error('No version number. Check experiment ID and perform db migration.')

        return new_exp

    def remove_experiment(self, exp_id):
        try:
            self.db.delete(self.db[exp_id])
        except couchdb.http.ResourceNotFound:
            logging.error(f'Could not find experiment {exp_id}')

    def upload_experiment(self, exp, overwrite = False):
        logging.info(f'Uploading {exp.id} to couchdb')
        doc = exp.jsonify()

        try:
            self.db.save(doc)
        except couchdb.http.ResourceConflict:
            if overwrite:
                self.remove_experiment(exp.id)
                self.db.save(doc)
                return

            logging.warning(f'Experiment "{exp.id}" already in database.')
            old_exp = self.pull_experiment(exp.id)

            merged_exp = Experiment(exp.id)
            if exp.hplc is not None:
                if old_exp.hplc is not None:
                    if input('Overwrite old HPLC data? Y/N\n').lower() == 'y':
                        merged_exp.hplc = exp.hplc
                    else:
                        merged_exp.hplc = old_exp.hplc
                else:
                    merged_exp.hplc = exp.hplc
            else:
                merged_exp.hplc = old_exp.hplc

            if exp.fplc is not None:
                if old_exp.fplc is not None:
                    if input('Overwrite old FPLC data? Y/N\n').lower() == 'y':
                        merged_exp.fplc = exp.fplc
                    else:
                        merged_exp.fplc = old_exp.fplc
                else:
                    merged_exp.fplc = exp.fplc
            else:
                merged_exp.fplc = old_exp.fplc

            self.remove_experiment(exp.id)
            doc = merged_exp.jsonify()
            self.db.save(doc)


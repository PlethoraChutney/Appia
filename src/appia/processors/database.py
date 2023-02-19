import couchdb
import logging
import pandas as pd
import sys
import os
import json
from appia.processors.experiment import Experiment
from appia.parsers.user_settings import appia_settings

class Database:
    def __init__(self) -> None:
        self.version = 4
        username = appia_settings.database_user
        password = appia_settings.database_password
        hostname = appia_settings.database_host
        port = appia_settings.database_port

        if any([x is None for x in [username, password, hostname, port]]):

            # deprecation handling 

            try:
                appia_settings.database_user = os.environ['COUCHDB_USERNAME']
                appia_settings.database_password = os.environ['COUCHDB_PASSWORD']
                appia_settings.database_host = os.environ['COUCHDB_HOST']
                appia_settings.save_settings()
                logging.info('Appia no longer uses environment variables for couchDB access. Your current environment variables have been saved to the new user settings system and are no longer required.')
                logging.info('To update these values in the future, run `appia utils --database-setup`')

                username = appia_settings.database_user
                password = appia_settings.database_password
                hostname = appia_settings.database_host
            except KeyError:
                try:
                    logging.info('Appia no longer uses separate JSON files for couchDB login. If you use an Appia config file, please enter the location below to transfer the information to the new user settings system. Otherwise, leave the entry blank.')
                    old_settings = input('Location of config.json: ')
                    old_settings = os.path.expanduser(old_settings)
                    if len(old_settings) == 0:
                        logging.error('Please run `appia utils --database-setup` to input database access information manually')
                        sys.exit(10)
                        
                    with open(old_settings, 'r') as settings_file:
                        old_config = json.load(settings_file)

                    appia_settings.database_user = old_config['user']
                    appia_settings.database_password = old_config['password']
                    appia_settings.database_host = old_config['host']
                    appia_settings.save_settings()

                    username = appia_settings.database_user
                    password = appia_settings.database_password
                    hostname = appia_settings.database_host
                
                except (FileNotFoundError, KeyboardInterrupt):
                    logging.error('Could not locate old Appia config file.')
                    logging.error('Please run `appia utils --database-setup` to input database access information manually')
                    sys.exit(10)
                except KeyError:
                    logging.error('Config file was missing couchDB access info.')
                    logging.error('Please run `appia utils --database-setup` to input database access information manually')
                    sys.exit(11)

        couchserver = couchdb.Server(f'http://{username}:{password}@{hostname}:{port}')

        dbname = 'traces'
        if dbname in couchserver:
            self.db = couchserver[dbname]
        else:
            self.db = couchserver.create(dbname)

    def __repr__(self) -> str:
        return f'CouchDB at {appia_settings.database_host}'

    def update_experiment_list(self):
        return [x['id'] for x in self.db.view('_all_docs')]


    def pull_experiment(self, id):
        doc = self.db.get(id)
        new_exp = Experiment(id)

        try:
            logging.debug(f'DB version: {self.version}\nExp version: {doc["version"]}')

            if doc['version'] == self.version:
                new_exp.hplc = pd.read_json(doc['hplc']).melt(
                id_vars = ['mL', 'Channel', 'Time', 'Normalization'],
                var_name = 'Sample',
                value_name = 'Value'
            )
            
            elif doc['version'] == 3:
                logging.info(f'{id} is a v3 Experiment. You should re-upload this Experiment.')
                new_exp.hplc = pd.read_json(doc['hplc'])

            elif doc['version'] != self.version:
                logging.error('Out of date experiment. Perform db migration.')

        except ValueError:
            pass
        except KeyError:
            logging.error('No version number. Check experiment ID and perform db migration.')


        try:
            new_exp.fplc = pd.read_json(doc['fplc'])
        except ValueError:
            pass
        except KeyError:
            new_exp.fplc = None


        return new_exp

    def remove_experiment(self, exp_id):
        try:
            self.db.delete(self.db[exp_id])
        except couchdb.http.ResourceNotFound:
            logging.error(f'Could not find experiment {exp_id}')

    def upload_experiment(self, exp, overwrite = False):
        logging.info(f'Uploading {exp} to {self}')
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

    def migrate(self):
        if input(f'To migrate database hosted at {appia_settings.database_host}, type: I have backed up my db\n').lower() == 'i have backed up my db':
            for exp_name in self.update_experiment_list():
                exp = self.pull_experiment(exp_name)
                self.upload_experiment(exp, overwrite=True)
        else:
            logging.warning('Back up your database before migrating it.')

db = Database()
import couchdb
from experiment import Experiment

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

def pull_experiment(db, id):
    doc = db.get(id)
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
        elif doc['version'] != 3:
            logging.error('Out of date experiment. Perform db migration.')
    except KeyError:
        logging.error('No version number. Check experiment ID and perform db migration.')

def remove_experiment(db, exp_id):
    try:
        db.delete(db[exp_id])
    except couchdb.http.ResourceNotFound:
        logging.error(f'Could not find experiment {exp_id}')

def upload_to_couchdb(exp, db, overwrite = False):
    logging.info(f'Uploading {exp.id} to couchdb')
    doc = exp.jsonify()

    try:
        db.save(doc)
    except couchdb.http.ResourceConflict:
        if overwrite:
            remove_experiment(exp.id)
            db.save(doc)
            return

        logging.warning(f'Experiment "{exp.id}" already in database.')
        old_exp = pull_experiment(db, exp.id)

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
            merged_exp.hplc = old.hplc

        if exp.fplc is not None:
            if old_exp.fplc is not None:
                if input('Overwrite old FPLC data? Y/N\n').lower() == 'y':
                    merged_exp.fplc = exp.fplc
                else:
                    merged_exp.fplc = old_exp.fplc
            else:
                merged_exp.fplc = exp.fplc
        else:
            merged_exp.fplc = old.fplc

        remove_experiment(exp.id)
        doc = merged_exp.jsonify()
        db.save(doc)


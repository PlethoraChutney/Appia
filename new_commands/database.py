from experiment import Experiment

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

def upload_to_couchdb(exp, db, overwrite = False):
    logging.info(f'Uploading {exp.id} to couchdb')
    doc = exp.jsonify()

    try:
        db.save(doc)
    except couchdb.http.ResourceConflict:
        logging.warning(f'Experiment "{exp.id}" already in database.')
import argparse
from processors.database import Database, Config
from processors.core import three_column_print

def main(args):
    if args.config == 'env':
        db = Database(Config())
    else:
        db = Database(Config(args.config))

    if args.list:
        three_column_print(db.update_experiment_list())

    if args.delete:
        for id in args.delete:
            db.remove_experiment(id)

    if args.inspect:
        for id in args.inspect:
            exp = db.pull_experiment(id)
            print(exp)
            exp.show_tables()

    if args.download:
        for id in args.download:
            exp = db.pull_experiment(id)
            exp.save_csvs('.')

parser = argparse.ArgumentParser(
    description = 'Database management',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    'config',
    help = 'Config JSON file',
    type = str
)
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
    '-i', '--inspect',
    help = 'Print information about experiments',
    type = str,
    nargs = '+'
)
parser.add_argument(
    '--download',
    help = 'Save experiments from the database as a .csv. Note that these may have been downsampled.',
    type = str,
    nargs = '+'
)
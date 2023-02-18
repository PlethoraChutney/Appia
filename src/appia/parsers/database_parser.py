import argparse
import os
from appia.processors.core import three_column_print

def main(args):

    from appia.processors.database import db

    if args.list or args.check_versions:
        list = db.update_experiment_list()
        if args.check_versions:
            out_of_date = False
            for exp_id in list:
                try:
                    version = db.db.get(exp_id)['version']
                except KeyError:
                    version = 0
                if version != db.version:
                    out_of_date = True
                    print(f'Experiment {exp_id} is version {version}')
            if not out_of_date:
                print('All versions match.')
        if args.list:
            three_column_print(list)

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
            exp.save_csvs(os.getcwd())

    if args.migrate:
        db.migrate()


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
parser.add_argument(
    '--check-versions',
    help = 'List experiments, categorized by version.',
    action = 'store_true'
)
parser.add_argument(
    '--migrate',
    help = 'Download and upload all experiments to migrate them to a new version. Back up first!!!',
    action = 'store_true'
)
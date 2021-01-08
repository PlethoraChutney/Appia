from subcommands import assemble_hplc, assemble_fplc
from glob import glob
import os
import argparse
import logging


def combined_df(files, h_system):
    system_extensions = {
        'waters': '.arw',
        'shimadzu': '.asc'
    }

    globbed_files = []
    for pattern in files:
        globbed_files.extend(glob(pattern))
    files = [os.path.abspath(x) for x in globbed_files]

    for file in files:
        try:
            assert file.lower().endswith(('.csv', system_extensions[h_system]))
        except AssertionError:
            logging.warning(f'Unexpected file extension in {file}. Did you set the right system?')
    print(files)

def main(args):
    cdf = combined_df(args.files, str.lower(args.system))

parser = argparse.ArgumentParser(
    description = 'Combined FPLC and HPLC processing',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    'files',
    help = 'All files to combine and process.',
    type = str,
    nargs = '+'
)
parser.add_argument(
    '--system',
    default = 'waters',
    help = 'What HPLC system. Default Waters',
    type = str
)

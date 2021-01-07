from subcommands import assemble_hplc, assemble_fplc
from glob import glob
import os
import argparse
import logging


def combined_df(files, h_system):
    files = [os.path.abspath(x) for x in glob(files)]
    return files

def main(args):
    cdf = combined_df(args.files, args.system)
    logging.debug(cdf)

parser = argparse.ArgumentParser(
    description = 'Combined FPLC and HPLC processing',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    'files',
    help = 'All files to combine and process.',
    type = str
)
parser.add_argument(
    '--system',
    default = 'waters',
    help = 'What HPLC system. Default Waters',
    type = str
)

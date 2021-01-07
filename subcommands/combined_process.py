from subcommands import assemble_hplc, assemble_fplc
import argparse
import logging


def main(args):
    if args.test:
        print('Yeah everything is working')

parser = argparse.ArgumentParser(
    description = 'Combined FPLC and HPLC processing',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    '-t', '--test',
    help = 'Test if this works',
    action = 'store_true'
)

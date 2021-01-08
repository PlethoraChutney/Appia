#!/usr/bin/env python3
import argparse
import logging

from subcommands.assemble_fplc import parser as fplc_parser
from subcommands.assemble_hplc import parser as hplc_parser
from subcommands.assemble_three_d import parser as three_d_parser
from subcommands.combined_process import parser as combined_parser
from subcommands.backend import parser as backend_parser

def main():
    parser = argparse.ArgumentParser(
        description = 'Process chromatography data from AKTA or Waters instruments'
    )
    subparsers = parser.add_subparsers()

    subparsers.add_parser(
        name = 'hplc',
        help = 'Process HPLC files (.arw)',
        parents = [hplc_parser]
    )
    subparsers.add_parser(
        name = 'fplc',
        help = 'Process FPLC files (.csv)',
        parents = [fplc_parser]
    )
    subparsers.add_parser(
        name = 'three-d',
        help = 'Process three dimensional HPLC files (.arw)',
        parents = [three_d_parser]
    )
    subparsers.add_parser(
        name = 'combined',
        help = 'Combine HPLC and FPLC processing into a single experiment.',
        parents = [combined_parser]
    )
    subparsers.add_parser(
        name = 'db',
        help = 'Database management',
        parents = [backend_parser]
    )
    parser.add_argument(
        '-v', '--verbose',
        help = 'Get more informational messages',
        action = 'count',
        default = 0
    )

    args = parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(len(levels) - 1, args.verbose)]
    logging.basicConfig(level = level, format = '%(levelname)s: %(message)s')

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

if __name__ == '__main__':
    main()

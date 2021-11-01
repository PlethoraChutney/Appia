#!/usr/bin/env python3
import argparse
import logging
import sys
from gooey import Gooey, GooeyParser

from parsers.process_parser import parser as process_parser
from parsers.database_parser import parser as db_parser

main_parser = GooeyParser(
    description = 'Process chromatography data and visualize it on the web.'
)
subparsers = main_parser.add_subparsers()

verbosity = main_parser.add_argument_group('Verbosity')
vxg = verbosity.add_mutually_exclusive_group()
vxg.add_argument(
    '-q', '--quiet',
    help = 'Print Errors only',
    action = 'store_const',
    dest = 'verbosity',
    const = 'q'
)
vxg.add_argument(
    '-v', '--verbose',
    help = 'Print Info, Warnings, and Errors. Default state.',
    action = 'store_const',
    dest = 'verbosity',
    const = 'v'
)
vxg.add_argument(
    '--debug',
    help = 'Print debug output.',
    action = 'store_const',
    dest = 'verbosity',
    const = 'd'
)

subparsers.add_parser(
    name = 'process',
    help = 'Process data',
    parents = [process_parser]
)
subparsers.add_parser(
    name = 'database',
    help = 'Manage CouchDB',
    parents = [db_parser]
)

@Gooey(
    program_name = 'Appia',
    default_size = (1080,720)
)
def main():
    args = main_parser.parse_args()

    levels = {
        'q': logging.ERROR, 
        'v': logging.INFO,
        'd': logging.DEBUG
    }
    try:
        level = levels[args.verbosity]
    except KeyError:
        level = logging.INFO

    logging.basicConfig(
        level = level,
        format = '{levelname}: {message} ({filename})',
        style = '{'
    )

    if 'func' in args:
        args.func(args)
    else:
        main_parser.print_help()

if __name__ == '__main__':
    main()
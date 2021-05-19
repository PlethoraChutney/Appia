import argparse
import logging

from parsers.process_parser import parser as process_parser
from parsers.database_parser import parser as db_parser

main_parser = argparse.ArgumentParser(
    description = 'Process chromatography data and visualize it on the web.'
)
subparsers = main_parser.add_subparsers()

main_parser.add_argument(
    '-v', '--verbose',
    help = 'Get more informational messages',
    action = 'count',
    default = 0
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

def main():
    args = main_parser.parse_args()

    levels = [logging.WARNING, logging.INFO, logging.DEBUG]
    level = levels[min(len(levels) - 1, args.verbose)]
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
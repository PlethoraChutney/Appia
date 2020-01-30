import argparse

from subcommands.assemble_fplc import parser as fplc_parser
from subcommands.assemble_hplc import parser as hplc_parser
from subcommands.assemble_three_d import parser as three_d_parser

if __name__ == '__main__':
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

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()

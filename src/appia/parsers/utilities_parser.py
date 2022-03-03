import argparse
import os
import shutil

def main(args):
    if args.copy_manual is not None:
        script_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

        shutil.copyfile(
                os.path.join(script_location, args.copy_manual, 'manual_plot_HPLC.R'),
                os.path.join(os.getcwd(), f'manual-plot-HPLC.R')
        )

        shutil.copyfile(
            os.path.join(script_location, args.copy_manual, 'manual_plot_FPLC.R'),
            os.path.join(os.getcwd(), f'manual-plot-FPLC.R')
        )

parser = argparse.ArgumentParser(
    'Appia utilities',
    add_help=False
)
parser.set_defaults(func = main)

parser.add_argument(
    '-c', '--copy-manual',
    help = 'Copy R manual plotting template. Argument is directory in which template resides, relative to Appia root.',
    nargs = '?',
    const = 'plotters'
)
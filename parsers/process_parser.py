import argparse
import os
from processors import hplc, fplc, experiment

def main(args):
    print(args)

parser = argparse.ArgumentParser(
    description = 'Process chromatography data',
    add_help = False    
)
parser.set_defaults(func = main)

parser.add_argument(
    'files',
    default = os.path.join(os.getcwd(), '*'),
    help = 'Glob or globs to find data files. For instance, "./*.arw"',
    nargs = '+'
)
parser.add_argument(
    '-i', '--id',
    help = 'Experiment ID. Default to name of HPLC Sample Set (if present) or FPLC file name.',
    type = str
)
parser.add_argument(
    '-r', '--reduce',
    help = 'Reduce web HPLC data points to this many total. Default 1000. CSV files are saved at full temporal resolution regardless.'
)
parser.add_argument(
    '-d', '--no-db',
    help = 'Do not upload experiment to couchdb'
)
parser.add_argument(
    '-n', '--normalize',
    help = 'Range over which to normalize in mL.',
    nargs = 2,
    type = float,
    default = [0.5, 1000]
)
parser.add_argument(
	'-c', '--copy-manual',
	help = 'Copy R plot file for manual plot editing',
	action = 'store_true',
	default = False
)
parser.add_argument(
	'-k', '--no-move',
	help = 'Process data files in place (do not move to new directory)',
	action = 'store_true',
	default = False
)
parser.add_argument(
	'--overwrite',
	help = "Overwrite database copy of experiment",
	action = 'store_true'
)
parser.add_argument(
    '-f', '--fractions',
    nargs = 2,
    default = [0, 0],
    type = int,
    help = 'Inclusive range of auto-plot SEC fractions to fill in. Default is none.'
)
parser.add_argument(
    '-m', '--ml',
    nargs = 2,
    default = [5, 25],
    type = int,
    help = 'Inclusive range for auto-plot x-axis, in mL. Default is 5 to 25. 0 0 selects full range.'
)

plot_group = parser.add_mutually_exclusive_group()
plot_group.add_argument(
    '-p', '--no-plots',
    help = 'Do not make default R plots',
    action = 'store_true',
    default = False
)
plot_group.add_argument(
	'-s', '--post-to-slack',
	help = "Send completed plots to Slack",
	action = 'store_true',
	default = False
)
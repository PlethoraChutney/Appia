import argparse
import os
import sys
import logging
import shutil
from appia.processors import hplc, fplc, experiment, core
from appia.plotters import auto_plot
from appia.processors.gui import user_input

def main(args):
    from appia.processors.database import db
    file_list = core.get_files(args.files)
    logging.debug(file_list)

    # Make Experiment ------------------------------------------------------------
    if args.id:
        exp = experiment.Experiment(args.id)
    
    
    if file_list['waters']:
        waters, wat_sample_set = hplc.append_waters(file_list['waters'], args.hplc_flow_rate)
        if wat_sample_set is None:
            wat_sample_set = user_input('Sample set name: ')

        waters['Value'] = waters['Value'] * args.scale_hplc

        try:
            exp.hplc = waters
        except NameError:
            exp = experiment.Experiment(wat_sample_set)
            exp.hplc = waters

    if file_list['shimadzu']:
        channel_mapping = {}
        i = 0
        while i < len(args.channel_mapping):
            channel_mapping[args.channel_mapping[i]] = args.channel_mapping[i+1]
            i += 2

        shim, shim_sample_set = hplc.append_shim(file_list['shimadzu'], channel_mapping, args.hplc_flow_rate)

        shim['Value'] = shim['Value'] * args.scale_hplc

        try:
            exp.extend_hplc(shim)
        except NameError:
            exp = experiment.Experiment(shim_sample_set)
            exp.hplc = shim

    if file_list['akta']:
        fplc_trace = fplc.append_fplc(file_list['akta'], args.fplc_cv)
        # everything but the '.csv' at the end from the first file name without directory info
        fplc_id = os.path.split(file_list['akta'][0])[1][:-4]

        try:
            exp.fplc = fplc_trace
        except NameError:
            exp = experiment.Experiment(fplc_id)
            exp.fplc = fplc_trace
            
    if file_list['agilent']:
        agil = hplc.append_agilent(file_list['agilent'], args.hplc_flow_rate)

        agil['Value'] = agil['Value'] * args.scale_hplc

        try:
            exp.extend_hplc(agil)
        except NameError:
            sample_set_name = user_input('Please provide an experiment name: ')
            exp = experiment.Experiment(sample_set_name)
            exp.hplc = agil

    try:
        logging.info(f'Made {exp}')
    except NameError:
        logging.error('Cannot make empty experiment.')
        sys.exit(1)

    if args.output_dir:
        out_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    elif not args.no_move:
        out_dir = os.path.abspath(os.path.join(os.curdir, exp.id))
    else:
        out_dir = os.path.curdir
        
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    for file_type in file_list.keys():
        if not args.no_move and file_list[file_type]:
            out = os.path.join(out_dir, f'{exp.id}_raw-{file_type}')
            if not os.path.isdir(out):
                os.makedirs(out)

            for file in file_list[file_type]:
                shutil.move(file, os.path.join(out, os.path.basename(file)))
    try:
        exp.renormalize_hplc(args.normalize, args.strict_normalize)
    except ValueError:
        if args.strict_normalize:
            logging.warning('No HPLC data to normalize')
    hplc_csv, fplc_csv = exp.save_csvs(out_dir)
    if hplc_csv:
        logging.debug(f'HPLC: ' + hplc_csv)
    else:
        logging.debug('No HPLC csv')
    if fplc_csv:
        logging.debug(f'FPLC: ' + fplc_csv)
    else:
        logging.debug(f'No FPLC csv')

    # Make Plots -----------------------------------------------------------------
    
    script_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    
    if args.plots:
        if exp.hplc is not None:
            logging.info('Making HPLC plots')
            auto_plot.auto_plot_hplc(
                exp.hplc, args.ml, 'mL'
                ).write_image(
                    os.path.join(out_dir, f'{exp.id}_auto-plot-hplc.png'),
                    width = 1920,
                    height = 1080
                    )
        
        if exp.fplc is not None:
            logging.info('Making FPLC plot')
            auto_plot.auto_plot_fplc(
                exp.fplc, args.ml, args.fractions, 'mL'
                ).write_image(
                    os.path.join(out_dir, f'{exp.id}_auto-plot-fplc.png'),
                    width = 1920,
                    height = 1080
                    )

    if args.copy_manual is not None:
        if exp.hplc is not None:
            shutil.copyfile(
                os.path.join(script_location, args.copy_manual, 'manual_plot_HPLC.R'),
                os.path.join(out_dir, f'{exp.id}_manual-plot-HPLC.R')
            )
        if exp.fplc is not None:
            shutil.copyfile(
                os.path.join(script_location, args.copy_manual, 'manual_plot_FPLC.R'),
                os.path.join(out_dir, f'{exp.id}_manual-plot-FPLC.R')
            )

    if args.database:
        exp.reduce_hplc(args.reduce)
        db.upload_experiment(exp, args.overwrite)

parser = argparse.ArgumentParser(
    description = 'Process chromatography data',
    add_help = False    
)
parser.set_defaults(func = main)

file_io = parser.add_argument_group('File IO')

parser.add_argument(
    'files',
    help = 'Glob or globs to find data files. For instance, "traces/*.arw"',
    nargs = '+'
)
file_io.add_argument(
    '-i', '--id',
    help = 'Experiment ID. Default to name of HPLC Sample Set (Waters over Shimadzu, if present) or FPLC file name.',
    type = str
)
file_io.add_argument(
    '-o', '--output-dir',
    help = 'Directory in which to save CSVs and plots. Default makes a new dir with experiment name.'
)
file_io.add_argument(
	'-k', '--no-move',
	help = 'Process data files in place (do not move to new directory)',
	action = 'store_true',
	default = False
)
file_io.add_argument(
	'-c', '--copy-manual',
	help = 'Copy R template file for manual plot editing. Argument is directory relative to Appia root in which templates reside.',
	nargs = '?',
    const = 'plotters'
)

process_args = parser.add_argument_group('Processing Options')
process_args.add_argument(
    '--hplc-flow-rate',
    help = 'Manually override flow rate. Provide a single number in mL/min',
    type = float
)
process_args.add_argument(
    '--fplc-cv',
    help = 'Column volume for FPLC data. Default is 24 mL (GE/Cytiva 10/300 column).',
    type = int,
    default = 24
)
process_args.add_argument(
    '-n', '--normalize',
    help = 'Set maximum of this range (in mL) to 1',
    nargs = 2,
    type = float,
    default = [0.5, 1000]
)
process_args.add_argument(
    '--strict-normalize',
    help = 'Also set minimum of normalization range to 0',
    action = 'store_true',
    default = False
)
process_args.add_argument(
    '--channel-mapping',
    nargs = '+',
    default = ['A', 'Trp', 'B', 'GFP'],
    help = 'Channel mappings for old Shimadzu instruments. Default: A Trp B GFP'
)
process_args.add_argument(
    '--scale-hplc',
    help = 'Scale signal values by a factor. For instance, --scale 0.5 will reduce all signal values by 1/2. Could be used to compare instruments with different flow cell path lengths.',
    default = 1,
    type = float
)

web_up = parser.add_argument_group('Web Upload')

web_up.add_argument(
    '-r', '--reduce',
    help = 'Reduce web HPLC data points to this many total. Default 1000. CSV files are saved at full temporal resolution regardless.',
    type = int,
    default = 1000
)
web_up.add_argument(
    '-d', '--database',
    help = '''Upload experiment to couchdb. Must have set your parameters using `appia database`.''',
    action = 'store_true'
)
web_up.add_argument(
    '--overwrite',
    help = 'Overwrite database copy of experiment with same name without asking',
    action = 'store_true'
)

auto_plots = parser.add_argument_group('Auto Plots')
auto_plots.add_argument(
    '-p', '--plots',
    help = 'Make default plots',
    action = 'store_true',
    default = False
)
auto_plots.add_argument(
    '-f', '--fractions',
    nargs = '+',
    default = None,
    help = 'SEC fractions to fill in. Default is none. Giving two numbers fills inclusive range; a third sets interval. E.g., 2 10 2 fills even fractions between 2 and 10.'
)
auto_plots.add_argument(
    '-m', '--ml',
    nargs = 2,
    default = ['5', '25'],
    type = str,
    help = 'Inclusive range for auto-plot x-axis, in mL. Default is 5 to 25. To auto-set one limit, type `auto` instead of a number.'
)


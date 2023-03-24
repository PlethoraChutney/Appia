import argparse
import os
import sys
import logging
import shutil
import pandas as pd
from datetime import datetime
from appia.processors import hplc, fplc, experiment, core
from appia.plotters import auto_plot

def main(args):
    file_list = core.process_globs(args.files)
    num_files = len(file_list)
    hplc_processors = hplc.HplcProcessor.__subclasses__()
    fplc_processors = fplc.FplcProcessor.__subclasses__()
    processors = hplc_processors + fplc_processors
    processed_files = []

    for i, filename in enumerate(file_list):
        core.loading_bar(i + 1, num_files)
        claimed = [Proc(filename, **vars(args)) for Proc in processors]
        claimed = [x for x in claimed if x.claimed]

        if len(claimed) == 1:
            processed_files.append(claimed[0])
        elif len(claimed) > 1:
            logging.error(f'{filename} claimed by multiple processors. Skipping.')
        else:
            logging.warning(f'{filename} claimed by no processor. If it is not a chromatography trace, this is fine.')


    # Make Experiment ------------------------------------------------------------
    if args.id:
        exp_id = args.id
    else:
        exp_id = None
        i = 0
        while exp_id is None and i < len(processed_files):
            exp_id = processed_files[i].set_name
            i += 1
        
        if exp_id is None:
            exp_id = 'Processed-On_' + datetime.today().strftime('%Y-%m-%d_%H-%M-%S')

    exp = experiment.Experiment(exp_id)

    try:
        exp.hplc = pd.concat([x.df for x in processed_files if x.proc_type == 'hplc'])
    except ValueError:
        exp.hplc = None
    try:
        exp.fplc = pd.concat([x.df for x in processed_files if x.proc_type == 'fplc'])
    except ValueError:
        exp.fplc = None

    logging.debug('Experiment HPLC data:')
    logging.debug(exp.hplc)
    logging.debug('Experiment FPLC data:')
    logging.debug(exp.fplc)

    try:
        logging.info(f'Made {exp}')
    except NameError:
        logging.error('Your experiment is empty. Stopping.')
        sys.exit(1)

    # Set output dir --------------------------------

    if args.output_dir:
        out_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    elif not args.no_move:
        logging.debug('Determining raw data dir...')
        logging.debug(f'Exp id: {exp.id}')
        out_dir = os.path.abspath(os.path.join(os.curdir, exp.id.replace(os.path.sep, '-')))
        logging.debug(f'Outdir: {out_dir}')
    else:
        out_dir = os.path.curdir
        
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    # move raw files to subdir ---------------------------

    if not args.no_move:
        for claimed_file in processed_files:
            raw_data_dir = os.path.join(out_dir, f'{claimed_file.manufacturer}_raw-files')
            if not os.path.isdir(raw_data_dir):
                os.makedirs(raw_data_dir)

            new_file_path = os.path.join(raw_data_dir, os.path.basename(claimed_file.filename))

            shutil.move(claimed_file.filename, new_file_path)

    # rescale and renormalize whole experiment ------------------------

    if args.scale_hplc and exp.hplc is not None:
        exp.hplc['Value'] = exp.hplc['Value'] * args.scale_hplc

    try:
        exp.renormalize_hplc(args.normalize, args.strict_normalize)
    except ValueError:
        if args.strict_normalize:
            logging.warning('No HPLC data to normalize')

    # save csvs -------------------------------------------
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

    # copy the manual plotting script, if requested ----------------

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

    # upload to the database -------------------------------------

    if args.database:
        from appia.processors.database import db
        exp.reduce_hplc(args.reduce)
        db.upload_experiment(exp, args.overwrite)

    return exp

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
    '--prefer-detector',
    help = 'New Shimadzu: if two detectors have the same channel, prefer the one with this name.'
)
process_args.add_argument(
    '--agilent-channel-name',
    help = 'Channel name for Agilent channels. This will override the channel specified by filenames if you have both.'
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
    help = "Upload experiment to couchdb. Must have set your parameters using `appia database`.",
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


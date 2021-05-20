import argparse
import os
import sys
import logging
import subprocess
import shutil
from processors import hplc, fplc, experiment, core
from processors.database import Database, Config

def main(args):
    file_list = core.get_files(args.files)
    logging.debug(file_list)

    # Make Experiment ------------------------------------------------------------
    if args.id:
        exp = experiment.Experiment(args.id)
    
    
    if file_list['arw']:
        waters, wat_sample_set = hplc.append_waters(file_list['arw'])

        try:
            exp.hplc = waters
        except NameError:
            exp = experiment.Experiment(wat_sample_set)
            exp.hplc = waters

    if file_list['asc']:
        channel_mapping = {}
        i = 0
        while i < len(args.channel_mapping):
            channel_mapping[args.channel_mapping[i]] = args.channel_mapping[i+1]
            i += 2

        shim, shim_sample_set = hplc.append_shim(file_list['asc'], channel_mapping)

        try:
            exp.extend_hplc(shim)
        except NameError:
            exp = experiment.Experiment(shim_sample_set)
            exp.hplc = shim

    if file_list['csv']:
        fplc_trace = fplc.append_fplc(file_list['csv'])
        # everything but the '.csv' at the end from the first file name without directory info
        fplc_id = os.path.split(file_list['csv'][0])[1][:-4]

        try:
            exp.fplc = fplc_trace
        except NameError:
            exp = experiment.Experiment(fplc_id)
            exp.fplc = fplc_trace

    try:
        logging.info(f'Made {exp}')
    except NameError:
        logging.error('Cannot make empty experiment.')
        sys.exit(1)

    if args.output_dir:
        out_dir = os.path.abspath(os.path.expanduser(args.output_dir))
    else:
        out_dir = os.path.abspath(os.path.join(os.curdir, exp.id))
        
    if not os.path.isdir(out_dir):
        os.makedirs(out_dir)

    for file_type in file_list.keys():
        if not args.no_move:
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

    # Make Plots -----------------------------------------------------------------
    
    script_location = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    
    if not args.no_plots:
        if hplc_csv:
            logging.info('Making HPLC plots')
            subprocess.run([
                'Rscript', os.path.join(script_location,
                'plotters', 'auto_graph_HPLC.R'),
                os.path.normpath(hplc_csv),
                args.ml[0], args.ml[1]
            ],
            cwd = out_dir)
        
        if fplc_csv:
            logging.info('Making FPLC plot')
            subprocess.run([
                'Rscript', os.path.join(script_location,
                'plotters', 'auto_graph_FPLC.R'),
                os.path.normpath(fplc_csv),
                args.fractions[0], args.fractions[1],
                args.ml[0], args.ml[1],
                os.path.split(os.path.normpath(fplc_csv))[0],
                os.path.split(os.path.normpath(fplc_csv))[1][:-4]
            ],
            cwd = out_dir)

    if args.copy_manual:
        if exp.hplc is not None:
            shutil.copyfile(
                os.path.join(script_location, 'plotters', 'manual_plot_HPLC.R'),
                os.path.join(out_dir, f'{exp.id}_manual-plot-HPLC.R')
            )
        if exp.fplc is not None:
            shutil.copyfile(
                os.path.join(script_location, 'plotters', 'manual_plot_FPLC.R'),
                os.path.join(out_dir, f'{exp.id}_manual-plot-FPLC.R')
            )

    if args.config:
        db = Database(Config(args.config))

        exp.reduce_hplc(args.reduce)
        db.upload_experiment(exp, args.overwrite)

    if args.post_to_slack:
        config = Config(args.post_to_slack)

        if config.slack:
            from processors import slackbot

            client = slackbot.get_client(config)

            if client is not None:
                slackbot.send_graphs(
                    config,
                    client,
                    os.path.join(out_dir, 'fsec_traces.pdf')
                )


parser = argparse.ArgumentParser(
    description = 'Process chromatography data',
    add_help = False    
)
parser.set_defaults(func = main)

parser.add_argument(
    'files',
    default = os.path.join(os.getcwd(), '*'),
    help = 'Glob or globs to find data files. For instance, "traces/*.arw"',
    nargs = '+'
)
parser.add_argument(
    '-i', '--id',
    help = 'Experiment ID. Default to name of HPLC Sample Set (Waters over Shimadzu, if present) or FPLC file name.',
    type = str
)
parser.add_argument(
    '-o', '--output-dir',
    help = 'Directory in which to save CSVs and plots. Default makes a new dir with experiment name.'
)
parser.add_argument(
    '-r', '--reduce',
    help = 'Reduce web HPLC data points to this many total. Default 1000. CSV files are saved at full temporal resolution regardless.',
    type = int,
    default = 1000
)
parser.add_argument(
    '-d', '--database',
    help = 'Upload experiment to couchdb. Optionally, provide config file location. Default config location is "config.json" in appia directory.',
    dest = 'config',
    nargs = '?',
    const = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'config.json')
)
parser.add_argument(
    '--overwrite',
    help = 'Overwrite database copy of experiment with same name without asking',
    action = 'store_true'
)
parser.add_argument(
    '-n', '--normalize',
    help = 'Set maximum of this range (in mL) to 1',
    nargs = 2,
    type = float,
    default = [0.5, 1000]
)
parser.add_argument(
    '--strict-normalize',
    help = 'Also set minimum of normalization range to 0',
    action = 'store_true',
    default = False
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
    '--channel-mapping',
    nargs = '+',
    default = ['A', 'Trp', 'B', 'GFP'],
    help = 'Channel mappings for Shimadzu instruments. Default: A Trp B GFP'
)
parser.add_argument(
    '-f', '--fractions',
    nargs = 2,
    default = ['0', '0'],
    type = str,
    help = 'Inclusive range of auto-plot SEC fractions to fill in. Default is none.'
)
parser.add_argument(
    '-m', '--ml',
    nargs = 2,
    default = ['5', '25'],
    type = str,
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
	help = "Send completed plots to Slack. Need a config JSON with slack token and channel, same default as db.",
	nargs = '?',
    const = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'config.json')
)
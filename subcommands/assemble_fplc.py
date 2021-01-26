import numpy as np
import pandas as pd
import sys
import os
import argparse
import subprocess
import shutil
import logging
from glob import glob

# 1 Data import ----------------------------------------------------------------

def get_file_list(globs):
    globbed_files = []
    for pattern in globs:
        globbed_files.extend(glob(pattern))
    logging.debug(f'Globbed files: {globbed_files}')
    files = [os.path.abspath(x) for x in globbed_files if x.endswith('.csv')]
    files = list(set(files))
    logging.debug(f'Final file list: {files}')


    logging.info(f'Found {len(files)} files')

    return list(files)

# * 1.1 Data tidying -----------------------------------------------------------

def append_chroms(file_list):
    chroms = pd.DataFrame(columns = ['mL', 'Channel', 'Signal', 'Fraction', 'Sample'])
    for file in file_list:
        fplc_trace = pd.read_csv(
            file, skiprows = 1,
            header = [1],
            encoding = 'utf-16-le',
            delimiter = '\t',
            engine = 'python'
        )
        fplc_trace = fplc_trace.filter(regex = '(ml|mAU$|mS/cm$|\%$|Fraction)')
        columns = fplc_trace.columns

        # The AKTA exports data with several different ml columns, each with their
        # own name (like ml.2, ml.3, etc.). These are mL axes for each channel.
        # Unfortunately, they are different for each channel! So we need to keep
        # each and know which channel it goes with. Additionally, since users
        # don't have to export every channel every time, we can't hard code positions
        renaming = {}
        if 'mAU' in columns:
            au_column = columns.get_loc('mAU')
            renaming[columns[au_column-1]] = 'mL_mAU'
        if 'mS/cm' in columns:
            ms_column = columns.get_loc('mS/cm')
            renaming[columns[ms_column-1]] = 'mL_mScm'
        if '%' in columns:
            percent_column = columns.get_loc('%')
            renaming[columns[percent_column-1]] = 'mL_percentB'
        if 'Fraction' in columns:
            frac_column = columns.get_loc('Fraction')
            renaming[columns[frac_column-1]] = 'frac_mL'
        fplc_trace = fplc_trace.rename(columns = renaming)

        long_trace = pd.DataFrame(columns = ['mL', 'Channel', 'Signal'])
        if 'mAU' in columns:
            mau = pd.melt(fplc_trace, id_vars = ['mL_mAU'], value_vars = ['mAU'], var_name = 'Channel', value_name = 'Signal')
            mau = mau.rename(columns = {'mL_mAU':'mL'}).dropna()
            long_trace = long_trace.append(mau)
        if 'mS/cm' in columns:
            mscm = pd.melt(fplc_trace, id_vars = ['mL_mScm'], value_vars = 'mS/cm', var_name = 'Channel', value_name = 'Signal')
            mscm = mscm.rename(columns = {'mL_mScm':'mL'}).dropna()
            long_trace = long_trace.append(mscm)
        if '%' in columns:
            perc = pd.melt(fplc_trace, id_vars = 'mL_percentB', value_vars = '%', var_name = 'Channel', value_name = 'Signal')
            perc = perc.rename(columns = {'mL_percentB':'mL'}).dropna()
            perc['Channel'] = '%_B'
            long_trace = long_trace.append(perc)
        if "Fraction" in columns:
            frac = fplc_trace.filter(regex = 'rac').dropna()
            long_trace = pd.concat([long_trace.reset_index(drop=True), frac], axis = 1)

        long_trace['Sample'] = os.path.basename(file)

        long_trace['inst_frac'] = 1
        frac_mL = long_trace['frac_mL'].dropna()
        for i in range(len(frac_mL)):
            long_trace.loc[long_trace['mL'] > frac_mL[i], 'inst_frac'] = i + 2

        long_trace['Fraction'] = long_trace['inst_frac']
        long_trace.drop(['frac_mL', 'inst_frac'], inplace = True, axis = 1)

        # Hard code a Superose 6 10_300 CV
        long_trace['Column Volume'] = long_trace['mL']/24
        chroms = chroms.append(long_trace, ignore_index = True)

    return chroms

# 2 Main -----------------------------------------------------------------------

def main(args):

    script_path = os.path.dirname(os.path.realpath(__file__))
    file_list = get_file_list(args.file_list)
    dir = os.path.dirname(file_list[0])
    dir = os.path.abspath(dir)
    min_frac = str(args.fractions[0])
    max_frac = str(args.fractions[1])
    low_ml = str(args.ml[0])
    high_ml = str(args.ml[1])

# * 2.1 csv generation ---------------------------------------------------------

    outfile = os.path.abspath(args.output) if args.output else os.path.join(dir, 'fplcs.csv')
    outdir = os.path.dirname(outfile)
    if outfile[-4:] != '.csv':
        print('Please include the name of the file in outfile, i.e., \'path/to/[name].csv\'')
        sys.exit(1)

    if os.path.isfile(outfile):
        if input(f'Are you sure you want to overwrite the file {os.path.abspath(outfile)}?\n[Y]es / [N]o\n').upper() != 'Y':
            sys.exit(0)

    if args.mass_export:
        for file in file_list:
            newdir = file[:-4].replace(' ', '_')
            os.mkdir(newdir)
            subprocess.run(['python', os.path.join(script_path, "assemble_fplc.py"), file, '--copy-manual', '-o', os.path.join(newdir, "fplcs.csv"), '-d'])
            shutil.move(file, os.path.join(newdir, file))
        sys.exit(0)

    logging.info('Generating compiled trace csv...')
    compiled = append_chroms(file_list)

    compiled.to_csv(outfile, index = False)

    if not args.no_db:
        if len(file_list) > 1:
            logging.error('Only upload experiments with one FPLC trace. You can combine them in the web interface.')
            sys.exit(2)
        from subcommands import backend, config
        logging.info('Uploading to database')

        to_upload = compiled[compiled.Channel == 'mAU']
        to_upload = to_upload[to_upload.mL < 24.5]

        id = os.path.split(file_list[0])[1][:-4].replace(' ', '_')

        db = backend.init_db(config.config)
        exp = backend.Experiment(id, None, to_upload)
        exp.upload_to_couchdb(db)

    if args.wide_table:
        compiled.pivot('mL', 'Channel', 'Signal').to_csv(newdir + '_wide.csv')
    logging.info('Done with csv...')

# * 2.2 Plots ------------------------------------------------------------------

    if not args.no_plots:
        logging.info(f'Generating plots ({low_ml} to {high_ml}mL, fractions {min_frac} to {max_frac})...')
        subprocess.run(['Rscript', os.path.join(script_path, 'auto_graph_FPLC.R'), outfile, min_frac, max_frac, low_ml, high_ml])
        if os.path.isfile(os.path.join(outdir, 'Rplots.pdf')) :
            os.remove(os.path.join(outdir, 'Rplots.pdf'))

    if args.copy_manual:
        logging.info('Copying manual RScript...')
        shutil.copyfile(os.path.join(script_path, 'manual_plot_FPLC.R'), os.path.join(outdir, 'manual_plot_FPLC.R'))
    logging.info('Done.')

parser = argparse.ArgumentParser(
    description = 'A script to collect FPLC traces from GE AKTA FPLCs',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    'file_list',
    help = 'Files to compare.',
    nargs = '+'
)
parser.add_argument(
    '-o', '--output',
    help = 'Where to write the compiled traces. Default is fplcs.csv in the first input directory'
)
parser.add_argument(
    '-f', '--fractions',
    nargs = 2, default = ['0', '0'],
    help = 'Inclusive range of fractions to fill in. Default is not to fill any.'
)
parser.add_argument(
    '-m', '--ml',
    nargs = 2, default = ['5', '25'],
    help = 'Inclusive range for x-axis, in mL. Default is 5 to 25'
)
parser.add_argument(
    '-c', '--copy-manual',
    help = 'Copy the manual plotting Rscript for further tweaking', action = 'store_true')
parser.add_argument(
    '-p', '--no-plots',
    help = 'Don\'t make R plots.', action = 'store_true'
)
parser.add_argument(
    '--wide-table',
    help= 'Save an additional table that is in \'wide\' format.',
    action = 'store_true'
)
parser.add_argument(
    '-d', '--no-db',
    help = 'Do not upload to visualization database',
    action = 'store_true'
)
parser.add_argument(
    '--mass-export',
    help = 'Analyze each input file seperately. Default false. Will not make wide table, will copy manual R script and make default plots. Ignores -o, -s, -f, -m flags.',
    action = 'store_true'
)

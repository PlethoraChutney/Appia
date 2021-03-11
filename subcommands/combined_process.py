from subcommands import assemble_hplc, assemble_fplc, backend, config
from glob import glob
import os
import sys
import argparse
import logging


def combined_df(files, h_system):
    # including fplc in system extensions for ~*~* futureproofing *~*~
    if h_system == 'shimadzu':
        logging.error('Combined processing not currently supported for Shimadzu instruments')
        sys.exit(3)

    f_system = 'akta'
    system_extensions = {
        'akta': '.csv',
        'waters': '.arw',
        'shimadzu': '.asc'
    }

    globbed_files = []
    for pattern in files:
        globbed_files.extend(glob(pattern))
    files = [os.path.abspath(x) for x in globbed_files]
    files = set(files)
    hplc_files = []
    fplc_files = []

    for file in files:
        try:
            if file.endswith(system_extensions[f_system]):
                fplc_files.append(file)
            elif file.endswith(system_extensions[h_system]):
                hplc_files.append(file)
            else:
                raise KeyError
        except KeyError:
            logging.error(f'Unexpected file extension in {file}. Please check your system and file arguments.')
            sys.exit(1)

    # keep [0] because append_chroms returns a list of [long, wide] dfs
    if hplc_files:
        h_df = assemble_hplc.append_chroms(hplc_files, h_system)[0]
        if 'Column Volume' not in h_df:
            logging.error('Please re-export your HPLC data with the instrument method included. This is needed to calculate volume and CV for comparison with SEC data, which is reported in volume.')
            sys.exit(4)

        h_df.drop(['Time'], inplace = True, axis = 1)
    else:
        h_df = None

    # filter out unnecessary channels and the wash recordings from the AKTA
    if fplc_files:
        f_df = assemble_fplc.append_chroms(fplc_files)
        f_df = f_df[f_df.Channel == 'mAU']
        f_df = f_df[f_df.mL < 24.5]
    else:
        f_df = None

    return (h_df, f_df)


def main(args):
    db = backend.init_db(config.config)

    logging.info('Making combined dataframe')
    c_df = combined_df(args.files, args.system)
    logging.info('Done with df. Making and uploading experiment.')
    to_upload = backend.Experiment(args.experiment, c_df[0], c_df[1])
    to_upload.get_plotly()
    logging.debug(to_upload)
    to_upload.upload_to_couchdb(db)

parser = argparse.ArgumentParser(
    description = 'Combined FPLC and HPLC processing',
    add_help=False
)
parser.set_defaults(func = main)
parser.add_argument(
    'experiment',
    help = 'Name of combined experiment',
    type = str
)
parser.add_argument(
    'files',
    help = 'All files to combine and process.',
    type = str,
    nargs = '+'
)
parser.add_argument(
    '--system',
    default = 'waters',
    help = 'What HPLC system. Default Waters',
    type = str.lower,
    choices = ['waters', 'shimadzu']
)

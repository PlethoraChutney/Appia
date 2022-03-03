from math import floor
from glob import glob
import logging
import os

def loading_bar(current, total, extension = '', force = False):
    try:
        log_level = logging.root.level
    except NameError:
        log_level = 0

    if log_level <= 20 or force:
        try:
            percent = floor(current/total * 10)
        except ZeroDivisionError:
            percent = 10

        loading_str = '    ' * percent + '><((((°>'

        print(f'{loading_str:<48}*  {current}/{total}', end = f'{extension}\r')
        if current == total:
            print()

def get_files(globs):
    globbed_files = []
    
    if isinstance(globs, str):
        globbed_files.extend(glob(globs))
    else:
        for pattern in globs:
            globbed_files.extend(glob(pattern))

    logging.debug(f'Globbed files: {globbed_files}')
    files = [os.path.abspath(x) for x in globbed_files]
    waters = [x for x in files if x.endswith('.arw')]
    shimadzu = [x for x in files if x.endswith('.asc') or x.endswith('.txt')]
    csv = [x for x in files if x.endswith('.csv') or x.endswith('.CSV')]

    agilent = []
    akta = []

    for file in csv:
        logging.debug(file)
        # process out csvs for agil and for akta
        try:
            with open(file, 'r', encoding = 'utf-8') as f:
                first_line = f.readline().strip().replace('\ufeff', '')
        except UnicodeDecodeError:
            with open(file, 'r', encoding = 'utf-16') as f:
                first_line = f.readline().strip().replace('\ufeff', '')

        if ',' in first_line:
            first_cell = first_line.split(',')[0]
        else:
            first_cell = first_line.split()[0]
        logging.debug(f'{file} first cell is {first_cell}')

        # AKTA files all have headers that say 'Chrom.1'
        if first_cell == 'Chrom.1':
            akta.append(file)
            logging.debug(f'{file} is an AKTA file')
        else:
            try:
                # if we can make a float from the first cell, it's an Agilent file
                float(first_cell.split()[0])
                agilent.append(file)
                logging.debug(f'{file} is an Agilent file')
            except ValueError:
                response = input(f'Could not determine filetype for {file}. (A)kta, A(g)ilent, or (S)kip?\n').lower()
                
                if response == 'a':
                    akta.append(file)
                elif response == 'g':
                    agilent.append(file)      

    return {
        'waters': waters,
        'shimadzu': shimadzu,
        'agilent': agilent,
        'akta': akta
    }

def normalizer(df, norm_range = None, strict = False):
    if not norm_range:
        norm_range = [0.5, df.mL.max()]

    ranged_df = df.loc[(df.mL > min(norm_range)) & (df.mL < max(norm_range))]
    if strict:
        min_sig = ranged_df.Signal.min()
    else:
        min_sig = df.Signal.min()

    max_sig = ranged_df.Signal.max()

    df['Normalized'] = (df.Signal - min_sig)/(max_sig - min_sig)
    df.Normalized = df.Normalized.fillna(0)

    return df

def three_column_print(in_list):
    in_list = iter(in_list)
    for i in in_list:
        print('{:<45}{:<45}{}'.format(i, next(in_list, ""), next(in_list, '')))

from math import floor
from glob import glob
import logging
import os
import pandas as pd

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

def process_globs(globs):
    globbed_files = []
    
    if isinstance(globs, str):
        globbed_files.extend(glob(globs))
    else:
        for pattern in globs:
            globbed_files.extend(glob(pattern))

    logging.debug(f'Globbed files: {globbed_files}')

    return globbed_files

def normalizer(df:pd.DataFrame, norm_range = None, strict = False):
    if not isinstance(df, pd.DataFrame):
        raise TypeError('df is not a pd.DataFrame')
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

from math import floor
from glob import glob
import logging
import os

def loading_bar(current, total, force = False):
    try:
        log_level = logging.root.level
    except NameError:
        log_level = 0

    if log_level > 20 and not force:
        pass
    else:
        percent = floor(current/total * 10)
        loading_str = '    ' * percent + '><((((°>'

        print(f'{loading_str:<48}*  {current}/{total}', end = '\r')
        if current == total:
            print()

def get_files(globs):
    globbed_files = []
    
    if isinstance(globs, str):
        globbed_files.extend(glob(globs))
    else:
        for pattern in globs:
            globbed_files.extend(glob(pattern))
            print(pattern)

    logging.debug(f'Globbed files: {globbed_files}')
    files = [os.path.abspath(x) for x in globbed_files]
    arw = [x for x in files if x.endswith('.arw')]
    asc = [x for x in files if x.endswith('.asc')]
    csv = [x for x in files if x.endswith('.csv')]

    return {'arw': arw,
            'asc': asc,
            'csv': csv}

import argparse
import os
import shutil
import logging
from appia.parsers.user_settings import appia_settings

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

    if args.flow_rate is not None:
        new_flow_rates = {}
        for fr_pair in args.flow_rate:
            try:
                new_flow_rates[fr_pair[0]] = float(fr_pair[1])
            except TypeError:
                logging.error('Bad flow rate. Give as --flow-rate {name} {mL/min number}')
                raise TypeError

        appia_settings.update_flow_rates(new_flow_rates)
        appia_settings.save_settings()

    if args.list_flow_rates:
        print('User specified flow rates:')
        for method, fr in appia_settings.flow_rates.items():
            print(f' {method + ":":>20} {fr}')
    
    if args.delete_flow_rate:
        for fr_key in args.delete_flow_rate:
            appia_settings.delete_flow_rate(fr_key)

        appia_settings.save_settings()

    if args.database_setup:
        print("Setting up database. To leave any of these settings unchanged, leave them blank.")

        new_settings = {}
        new_settings['database_host'] = input('Database host (something like blah.domain.edu): ')
        new_settings['database_user'] = input('Database username. (You set this during the docker installation): ')
        new_settings['database_password'] = input('Database password. (You set this during the docker installation): ')
        port = input("Database port number. (If you don't know, it's the default so leave it blank): ")
        new_settings['database_port'] = port if len(port) == 0 else int(port)

        for setting, value in new_settings.items():
            logging.debug(f'Setting {setting} is {value}')
            if isinstance(value, int) or len(value) > 0:
                setattr(appia_settings, setting, value)

        appia_settings.save_settings()
    
    if args.check_database_login:
        print('Host:', appia_settings.database_host)
        print('Username:', appia_settings.database_user)
        print('Password:', appia_settings.database_password)
        print('Port:', appia_settings.database_port)


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
parser.add_argument(
    '-f', '--flow-rate',
    help = 'Add a default flow rate for a method to skip manual input. Give a unique part of the method name and a flow rate in mL/min. For instance, `--flow-rate Sup6_10-300 0.5` would automatically set flow rates for all HPLC files with that string in their name (e.g., Sup6_10-300_20221202) to 0.5 mL/min unless manually set to something else.',
    nargs = 2,
    action = 'append'
)
parser.add_argument(
    '--list-flow-rates',
    help = 'Check current user flow rate values.',
    action = 'store_true'
)
parser.add_argument(
    '--delete-flow-rate',
    help = 'Remove a flow rate from user settings. Give the method names. Can give multiple method names.',
    nargs='+'
)
parser.add_argument(
    '--database-setup',
    help = 'Set database access parameters',
    action = 'store_true'
)
parser.add_argument(
    '--check-database-login',
    help = 'Print login info to the terminal',
    action = 'store_true'
)
import json
import os
import logging

class AppiaSettings(object):
    def __init__(self, settings_path=None) -> None:
        if settings_path is None:
            settings_path = os.path.expanduser('~/.appia-settings.json')

        self.settings_path = settings_path

        try:
            with open(settings_path, 'r') as f:
                self._user_settings = json.load(f)
        except FileNotFoundError:
            self._user_settings = {}

    def save_settings(self):
        with open(self.settings_path, 'w') as f:
            json.dump(self._user_settings, f)

    # Flow rates --------------------------------------------------------

    @property
    def flow_rates(self) -> dict:
        return self._user_settings.get('flow_rates', {})

    @flow_rates.setter
    def flow_rates(self, new_flow_rates:dict):
        if isinstance(new_flow_rates, dict):
            self._user_settings['flow_rates'] = new_flow_rates
        else:
            raise TypeError(f'Flow rates must be a dict, not a {type(new_flow_rates)}')

    def delete_flow_rate(self, method_name):
        del self._user_settings['flow_rates'][method_name]

    def update_flow_rates(self, new_flow_rates:dict):
        old_flow_rates = self.flow_rates
        old_flow_rates.update(new_flow_rates)
        self.flow_rates = old_flow_rates

    def check_flow_rate(self, method_name:str):
        matches = [x for x in self.flow_rates.keys() if x in method_name]
        logging.debug(f'Matches: {matches}')
        if len(matches) == 1:
            return self.flow_rates[matches[0]]
        elif len(matches) > 1:
            logging.warning(f'More than one match for {method_name}')

        return None
    
    # FPLC column volumes

    @property
    def default_column_volume(self):
        return self._user_settings.get('default_column_volume')

    @default_column_volume.setter
    def default_column_volume(self, cv):
        if isinstance(cv, float) or cv is None:
            self._user_settings['default_column_volume'] = cv
            self.save_settings()
        else:
            raise TypeError('Column volume must be a number')
    
    # Database -------------------------------------------------------------

    @property
    def database_host(self):
        return self._user_settings.get('database_host')
        
    @database_host.setter
    def database_host(self, hostname:str):
        if isinstance(hostname, str):
            self._user_settings['database_host'] = hostname
        else:
            raise TypeError(f'Hostname must be a string, not a {type(hostname)}')
        
    @property
    def database_port(self):
        return self._user_settings.get('database_port', '5984')

    @database_port.setter
    def database_port(self, port:int):
        if isinstance(port, int):
            self._user_settings['database_port'] = str(port)
        else:
            raise TypeError(f'Port must be an integer, not a {type(port)}')
        
    @property
    def database_user(self):
        return self._user_settings.get('database_username')

    @database_user.setter
    def database_user(self, username:str):
        if isinstance(username, str):
            self._user_settings['database_username'] = username
        else:
            raise TypeError(f'Username must be a strong, not a {type(username)}')
        
    @property
    def database_password(self):
        return self._user_settings.get('database_password')

    @database_password.setter
    def database_password(self, password:str):
        if isinstance(password, str):
            self._user_settings['database_password'] = password
        else:
            raise TypeError(f'Password must be a string, not a {type(password)}')

    
appia_settings = AppiaSettings()
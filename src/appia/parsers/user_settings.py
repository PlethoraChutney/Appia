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

    @property
    def flow_rates(self) -> dict:
        try:
            return self._user_settings['flow_rates']
        except KeyError:
            return {}

    @flow_rates.setter
    def flow_rates(self, new_flow_rates:dict):
        if isinstance(new_flow_rates, dict):
            self._user_settings['flow_rates'] = new_flow_rates
        else:
            raise TypeError

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
import sys
import os
import logging
from slack import WebClient
from slack.errors import SlackApiError

def get_client(config):
    try:
        chromatography_channel = config['chromatography_channel']
    except KeyError as e:
        logging.error('Include the name or ID of your chromatography channel in config.\nSkipping slack integration.')
        return

    try:
        token = config['token']
        if config['token'] == '':
            logging.error('Config file has empty Slack token. Skiping slack integration.')
            return None
        client = WebClient(token = token)
        client.auth_test()
        logging.info('Slack authentication succeeded')
    except KeyError as e:
        logging.error('Your config file does not have a bot token. Cannot post to slack')
        return None
    except SlackApiError as e:
        if e.response['error'] == 'invalid_auth':
            logging.error('Slack bot authentication failed.')
        else:
            raise e

    return client

def send_graphs(config, client, files):
    try:
        chromatography_channel = config['chromatography_channel']
    except KeyError as e:
        logging.error('Include the name or ID of your chromatography channel in config.\nSkipping slack integration.')
        return

    client.chat_postMessage(
        channel = chromatography_channel,
        text = 'A chromatography run has completed!'
    )
    for file in files:
        client.files_upload(
            channels = chromatography_channel,
            file = file
        )

import logging
from slack import WebClient
from slack.errors import SlackApiError

def get_client(config):
    if 'chromatography_channel' not in config.keys():
        logging.error('Include the name or ID of your chromatography channel in config. Skipping Slack integration.')
        return

    try:
        token = config['token']
        assert token != ''
        client = WebClient(token = token)
        client.auth_test()
        logging.info('Slack authentication succeeded')
    except (KeyError, AssertionError):
        logging.error('Your config file does not have a bot token. Cannot post to Slack.')
        return None
    except SlackApiError as e:
        if e.response['error'] == 'invalid_auth':
            logging.error('Slack bot authentication failed. Check your token.')
            return
        else:
            raise e

    return client

def send_graphs(config, client, files):
    try:
        chromatography_channel = config['chromatography_channel']
        assert chromatography_channel != ''

        client.chat_postMessage(
            channel = chromatography_channel,
            text = 'A chromatography run has completed!'
        )
        for file in files:
            client.files_upload(
                channels = chromatography_channel,
                file = file
            )

    except (KeyError, AssertionError):
        logging.error('Include the name or ID of your chromatography channel in config. Skipping Slack integration.')
        return

    except SlackApiError as e:
        if e.response['error'] == 'channel_not_found':
            logging.error('Channel name or ID is not correct. Skipping Slack integration.')
            return
        else:
            raise e

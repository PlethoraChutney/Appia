import logging
from slack import WebClient
from slack.errors import SlackApiError

def get_client(config):
    try:
        assert config.slack_token != ''
        client = WebClient(token = config.slack_token)
        client.auth_test()
        logging.info('Slack authentication succeeded')
    except AssertionError:
        logging.error('Your config has a blank bot token. Cannot post to Slack.')
    except SlackApiError as e:
        if e.response['error'] == 'invalid_auth':
            logging.error('Slack bot authentication failed. Check your token.')
            return
        else:
            raise e

    return client

def send_graphs(config, client, files):
    try:
        assert config.slack_channel != ''

        client.chat_postMessage(
            channel = config.slack_channel,
            text = 'A chromatography run has completed!'
        )
        for file in files:
            client.files_upload(
                channels = config.slack_channel,
                file = file
            )

    except AssertionError:
        logging.error('Your config channel ID is blank. Cannot send messages.')
    except SlackApiError as e:
        if e.response['error'] == 'channel_not_found':
            logging.error('Channel name or ID is not correct. Cannot send messages.')
            return
        else:
            raise e
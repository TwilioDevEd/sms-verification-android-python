import os

from os.path import join, dirname
from dotenv import load_dotenv


class ConfigurationException(Exception):
    pass


def load_dotenv_configuration(app):
    if app.config['TESTING']:
        load_test_config(app)
    else:
        dotenv_path = join(dirname(__file__), '../.env')
        load_dotenv(dotenv_path)
        check_configuration(app)


def load_test_config(app):
    test_config = {
        'TWILIO_ACCOUNT_SID': "ACXXXXXXXXXX",
        'TWILIO_API_KEY': "SKXXXXXXXXXX",
        'TWILIO_API_SECRET': "super_api_super_secret",
        'SENDING_PHONE_NUMBER': "+15550421337",
        'APP_HASH': "fake",
        'CLIENT_SECRET': "secret",
        'CONFIGURATION_LOADED': True
    }
    app.config.update(test_config)


def check_configuration(app):
    _check_keys(
        app,
        ['TWILIO_API_KEY', 'TWILIO_API_SECRET', 'TWILIO_ACCOUNT_SID'],
        'Please copy the .env.example file to .env, ' +
        'and then add your Twilio API Key, API Secret, ' +
        'and Account SID to the .env file. ' +
        'Find them on https://www.twilio.com/console'
    )
    _check_key(
        app,
        'SENDING_PHONE_NUMBER',
        'Please provide a valid phone number, ' +
        'such as +15125551212, in the .env file'
    )
    _check_key(
        app,
        'APP_HASH',
        'Please provide a valid Android app hash, ' +
        'which you can find in the Settings menu item ' +
        'of the Android app, in the .env file'
    )
    _check_key(
        app,
        'CLIENT_SECRET',
        'Please provide a secret string to share, ' +
        'between the app and the server ' +
        'in the .env file'
    )
    app.config['CONFIGURATION_LOADED'] = True


def _check_keys(app, keys, message):
    for key in keys:
        _check_key(app, key, message)


def _check_key(app, key, message):
    if key not in os.environ or os.environ[key] == '':
        raise ConfigurationException(message)
    else:
        app.config[key] = os.environ[key]

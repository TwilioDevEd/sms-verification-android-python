# coding: utf-8
import logging
import sys

from functools import wraps
from flask import Flask, request, Response, jsonify
from twilio.rest import Client

from .config import load_dotenv_configuration, ConfigurationException
from .sms_verify import SMSVerify


logger = logging.getLogger(__name__)
app = Flask(__name__)


def setup_app(app):
    if not app.config.get('CONFIGURATION_LOADED', False):
        load_dotenv_configuration(app)
        app.twilio_client = Client(
            app.config['TWILIO_API_KEY'],
            app.config['TWILIO_API_SECRET'],
            account_sid=app.config['TWILIO_ACCOUNT_SID']
        )
        app.sms_verify = SMSVerify(
            app.twilio_client,
            app.config['SENDING_PHONE_NUMBER'],
            app.config['APP_HASH']
        )


def configuration_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            setup_app(app)
        except ConfigurationException as e:
            response = jsonify({'success': False, 'message': str(e)})
            response.status_code = 500
            logger.error(e)
            return response
        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/request', methods=['POST'])
@configuration_required
def api_request():
    """Send a one-time code to the user's phone number for verification."""
    data = request.get_json()
    if not data:
        raise InvalidRequest('POST data was expected to be JSON')
    if not all(param in data for param in ['client_secret', 'phone']):
        raise InvalidRequest('Both client_secret and phone are required.')
    if app.config['CLIENT_SECRET'] != data['client_secret']:
        raise InvalidRequest('The client_secret parameter does not match')
    app.sms_verify.request(data['phone'])
    return jsonify({'success': True, 'time': app.sms_verify.default_expiration})


@app.route('/api/verify', methods=['POST'])
@configuration_required
def api_verify():
    """Verify the one-time code for a phone number."""
    data = request.get_json()
    if not data:
        raise InvalidRequest('POST data was expected to be JSON')
    if not all(param in data for param in ['client_secret', 'phone', 'sms_message']):
        raise InvalidRequest('The client_secret, phone, and sms_message are required.')
    if app.config['CLIENT_SECRET'] != data['client_secret']:
        raise InvalidRequest('The client_secret parameter does not match')

    if app.sms_verify.verify(data['phone'], data['sms_message']):
        return jsonify({'success': True, 'phone': data['phone']})
    else:
        return jsonify({
            'success': False,
            'message': 'Unable to validate code for this phone number'
        })


@app.route('/api/reset', methods=['POST'])
@configuration_required
def api_reset():
    """Reset the one-time code for a phone number."""
    data = request.get_json()
    if not data:
        raise InvalidRequest('POST data was expected to be JSON')
    if not all(param in data for param in ['client_secret', 'phone']):
        raise InvalidRequest('The client_secret and phone are required')
    if app.config['CLIENT_SECRET'] != data['client_secret']:
        raise InvalidRequest('The client_secret parameter does not match')

    if app.sms_verify.reset(data['phone']):
        return jsonify({'success': True, 'phone': data['phone']})
    else:
        return jsonify({
            'success': False,
            'message': 'Unable to reset code for this phone number'
        })


class InvalidRequest(Exception):
    def __init__(self, message, status_code=400):
        super(Exception, self).__init__(message)
        self.status_code = status_code

    def to_dict(self):
        return {'success': False, 'message': str(self)}


@app.errorhandler(InvalidRequest)
def handle_invalid_request(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

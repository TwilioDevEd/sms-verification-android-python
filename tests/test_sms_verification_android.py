import json
import types
import unittest
from unittest.mock import MagicMock
from sms_verification_android import app, setup_app
from itertools import combinations


class SMSVerificationAndroidTestCase(unittest.TestCase):

    def setUp(self):
        app.config['TESTING'] = True
        setup_app(app)
        app.sms_verify.request = MagicMock()
        app.sms_verify.verify = MagicMock()
        app.sms_verify.reset = MagicMock()
        self.app = app.test_client()

    def check_common_api_request(self, path, data=None, status_code=200, success=True):
        response = self.app.post(
            '/api/{}'.format(path),
            data=json.dumps(data),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, status_code)
        data = json.loads(response.get_data())
        self.assertIn('success', data)
        self.assertEqual(data['success'], success)
        return data

    def check_invalid_api_request(self, path, data=None, status_code=400, success=False, message=None):
        data = self.check_common_api_request(path, data, status_code, success)
        self.assertIn('message', data)
        self.assertEqual(data['message'], message)
        return data

    #
    # Test Route : /api/request
    #
    def test_request_code_without_parameter(self):
        self.check_invalid_api_request(
            'request',
            message='POST data was expected to be JSON'
        )

    def test_request_code_with_missing_parameter(self):
        self.check_invalid_api_request(
            'request',
            data={'client_secret': 'fake'},
            message='Both client_secret and phone are required.'
        )
        self.check_invalid_api_request(
            'request',
            data={'phone': '+15550005555'},
            message='Both client_secret and phone are required.'
        )

    def test_request_code_with_invalid_secret(self):
        self.check_invalid_api_request(
            'request',
            data={'client_secret': 'lol', 'phone': '+15550005555'},
            message='The client_secret parameter does not match'
        )

    def test_request_code_with_correct_parameter(self):
        data = self.check_common_api_request(
            'request',
            data={'client_secret': 'secret', 'phone': '+15550005555'}
        )
        self.assertIn('time', data)
        app.sms_verify.request.assert_called_once_with('+15550005555')

    #
    # Test Route : /api/verify
    #
    def test_verify_code_without_parameter(self):
        self.check_invalid_api_request(
            'verify',
            message='POST data was expected to be JSON'
        )

    def test_verify_code_with_missing_parameter(self):
        parameters = [
            ('client_secret', 'fake'),
            ('phone', '+15550005555'),
            ('sms_message', 'fake sms')
        ]
        for parameter in parameters:
            self.check_invalid_api_request(
                'verify',
                data=dict([parameter]),
                message='The client_secret, phone, and sms_message are required.'
            )
        for combination in combinations(parameters, 2):
            self.check_invalid_api_request(
                'verify',
                data=dict(combination),
                message='The client_secret, phone, and sms_message are required.'
            )

    def test_verify_code_with_invalid_secret(self):
        self.check_invalid_api_request(
            'verify',
            data={
                'client_secret': 'lol',
                'phone': '+15550005555',
                'sms_message': 'fake sms'
            },
            message='The client_secret parameter does not match'
        )

    def test_verify_code_with_correct_parameter(self):
        app.sms_verify.verify.return_value = True
        data = self.check_common_api_request(
            'verify',
            data={
                'client_secret': 'secret',
                'phone': '+15550005555',
                'sms_message': 'fake sms'
            },
        )
        self.assertIn('phone', data)
        self.assertEqual(data['phone'], '+15550005555')
        app.sms_verify.verify \
           .assert_called_once_with('+15550005555', 'fake sms')

    def test_verify_code_with_correct_parameter_and_wrong_code(self):
        app.sms_verify.verify.return_value = False
        data = self.check_common_api_request(
            'verify',
            data={
                'client_secret': 'secret',
                'phone': '+15550005555',
                'sms_message': 'fake sms'
            },
            success=False
        )
        self.assertIn('message', data)
        self.assertEqual(
            data['message'],
            'Unable to validate code for this phone number'
        )
        app.sms_verify.verify \
           .assert_called_once_with('+15550005555', 'fake sms')

    #
    # Test Route : /api/reset
    #
    def test_reset_code_without_parameter(self):
        self.check_invalid_api_request(
            'reset',
            message='POST data was expected to be JSON'
        )

    def test_reset_code_with_missing_parameter(self):
        parameters = [
            ('client_secret', 'fake'),
            ('phone', '+15550005555')
        ]
        for parameter in parameters:
            self.check_invalid_api_request(
                'reset',
                data=dict([parameter]),
                message='The client_secret and phone are required'
            )

    def test_reset_code_with_invalid_secret(self):
        self.check_invalid_api_request(
            'reset',
            data={
                'client_secret': 'lol',
                'phone': '+15550005555',
            },
            message='The client_secret parameter does not match'
        )

    def test_reset_code_with_correct_parameter(self):
        app.sms_verify.reset.return_value = True
        data = self.check_common_api_request(
            'reset',
            data={
                'client_secret': 'secret',
                'phone': '+15550005555',
            },
        )
        self.assertIn('phone', data)
        self.assertEqual(data['phone'], '+15550005555')
        app.sms_verify.reset.assert_called_once_with('+15550005555')

    def test_reset_code_with_correct_parameter_and_wrong_code(self):
        app.sms_verify.reset.return_value = False
        data = self.check_common_api_request(
            'reset',
            data={
                'client_secret': 'secret',
                'phone': '+15550005555',
                'sms_message': 'fake sms'
            },
            success=False
        )
        self.assertIn('message', data)
        self.assertEqual(
            data['message'],
            'Unable to reset code for this phone number'
        )
        app.sms_verify.reset.assert_called_once_with('+15550005555')

import unittest
from unittest.mock import MagicMock
from sms_verification_android import SMSVerify


class SMSVerifyTestCase(unittest.TestCase):
    def setUp(self):
        self.twilio_client = MagicMock()
        self.twilio_client.messages.create = MagicMock()
        self.sending_phone_number = '+15550005555'
        self.phone_number = '+10123456789'
        self.otp = 123456
        self.app_hash = 'fake_hash'
        self.sms_verify = SMSVerify(self.twilio_client, self.sending_phone_number, self.app_hash)
        self.sms_verify.cache = MagicMock()

    def generate_sms_message(self, otp):
        return '[#] Use {otp} as your code for the app!\n{app_hash}'.format(
            otp=otp, app_hash=self.app_hash
        )

    def test_generate_one_time_code(self):
        code = self.sms_verify.generate_one_time_code()
        self.assertTrue(isinstance(code, int))
        self.assertRegex(str(code), r'^\d{6}$')

    def test_request(self):
        self.sms_verify.generate_one_time_code = MagicMock(return_value=self.otp)
        self.sms_verify.request(self.phone_number)
        self.sms_verify.cache.set.assert_called_once_with(
            self.phone_number,
            self.otp,
            self.sms_verify.default_expiration
        )
        self.twilio_client.messages.create.assert_called_once_with(
            body=self.generate_sms_message(self.otp),
            from_=self.sending_phone_number,
            to=self.phone_number
        )

    def test_verify_with_phone_without_otp(self):
        self.sms_verify.cache.get.return_value = None
        ret = self.sms_verify.verify(self.phone_number, 'fake')
        self.assertFalse(ret)
        self.sms_verify.cache.get.assert_called_once_with(self.phone_number)

    def test_verify_with_phone_with_correct_otp(self):
        self.sms_verify.cache.get.return_value = self.otp
        ret = self.sms_verify.verify(self.phone_number, self.generate_sms_message(self.otp))
        self.assertTrue(ret)
        self.sms_verify.cache.get.assert_called_once_with(self.phone_number)

    def test_verify_with_phone_with_incorrect_otp(self):
        self.sms_verify.cache.get.return_value = self.otp
        ret = self.sms_verify.verify(self.phone_number, self.generate_sms_message(self.otp + 1))
        self.assertFalse(ret)
        self.sms_verify.cache.get.assert_called_once_with(self.phone_number)

    def test_reset_with_phone_without_otp(self):
        self.sms_verify.cache.get.return_value = None
        ret = self.sms_verify.reset(self.phone_number)
        self.assertFalse(ret)
        self.sms_verify.cache.get.assert_called_once_with(self.phone_number)
        self.sms_verify.cache.pop.assert_not_called()

    def test_reset_with_phone_with_otp(self):
        self.sms_verify.cache.get.return_value = self.otp
        ret = self.sms_verify.reset(self.phone_number)
        self.assertTrue(ret)
        self.sms_verify.cache.get.assert_called_once_with(self.phone_number)
        self.sms_verify.cache.pop.assert_called_once_with(self.phone_number)
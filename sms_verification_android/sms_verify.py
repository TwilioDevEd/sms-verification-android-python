from math import floor, pow
from random import random
import logging
from .cache import Cache

logger = logging.getLogger(__name__)


class SMSVerify(object):
    def __init__(self, twilio_client, sending_phone_number, app_hash):
        self.twilio_client = twilio_client
        self.sending_phone_number = sending_phone_number
        self.app_hash = app_hash
        self.cache = Cache()
        self.default_expiration = 900

    def generate_one_time_code(self):
        codelength = 6
        code = floor(random() * (pow(10, (codelength - 1)) * 9)) + pow(10, (codelength - 1))
        return int(code)

    def request(self, phone):
        logger.info('Requesting SMS to be sent to ' + phone)

        otp = self.generate_one_time_code()
        self.cache.set(phone, otp, self.default_expiration)

        sms_message = '[#] Use {otp} as your code for the app!\n{appHash}'.format(
            otp=otp,
            appHash=self.app_hash
        )
        logger.info(sms_message)

        self.twilio_client.messages.create(
            to=phone,
            from_=self.sending_phone_number,
            body=sms_message
        )

    def verify(self, phone, sms_message):
        logger.info('Verifying {}: {}'.format(phone, sms_message))
        otp = self.cache.get(phone)
        if not otp:
            logger.info('No cached otp value found for phone: {}'.format(phone))
            return False
        if str(otp) in sms_message:
            logger.info('Found otp value in cache')
            return True
        else:
            logger.info('Mismatch between otp value found and otp value expected')
            return False

    def reset(self, phone):
        logger.info('Resetting code for: {}'.format(phone))
        otp = self.cache.get(phone)
        if not otp:
            logger.info('No cached otp value found for phone: {}'.format(phone))
            return False
        self.cache.pop(phone)
        return True

#!/usr/bin/env python
import logging

from flask_script import Manager, Server
from sms_verification_android import app

logging.basicConfig(level=logging.INFO)

manager = Manager(app)
manager.add_command('runserver', Server(host='0.0.0.0', port=3000))


@manager.command
def test():
    """Run the unit tests."""
    logging.disable(logging.CRITICAL)
    from unittest import defaultTestLoader, TextTestRunner
    tests = defaultTestLoader.discover('tests')
    TextTestRunner().run(tests)


if __name__ == '__main__':
    manager.run()

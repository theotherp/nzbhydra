from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import pytest
from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
import unittest

from nzbhydra.tests.db_prepare import set_and_drop


class LoggingCaptor(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.records = []
        self.messages = []
        
    
    def emit(self, record):
        self.records.append(record)
        self.messages.append(record.msg)

class LoggingTests(unittest.TestCase):
    
    @pytest.fixture
    def setUp(self):
        set_and_drop()
    
    def testThatSensitiveDataIsRemoved(self):
        from nzbhydra import config
        config.settings.main.apikey = "testapikey"
        config.settings.main.username = "asecretusername"
        config.settings.main.password = "somepassword"
 
        from nzbhydra.log import setup_custom_logger
        logger = setup_custom_logger("test")
        logging_captor = LoggingCaptor()
        logger.addHandler(logging_captor)
        
        logger.info("Test")
        logger.info("Using apikey=testapikey")
        logger.info("Using username=asecretusername")
        logger.info("Using password=somepassword")
        logger.info({"apikey": "testapikey"})
        
        
        self.assertEqual(logging_captor.records[0].message, "Test")
        self.assertEqual(logging_captor.records[1].message, "Using apikey=<APIKEY>")
        self.assertEqual(logging_captor.records[2].message, "Using username=<USER>")
        self.assertEqual(logging_captor.records[3].message, "Using password=<PASSWORD>")
        self.assertEqual(logging_captor.records[4].message, "{u'apikey': u'testapikey'}")
        
        logger.error("An error that should be visible on the console")
        logger.info("A text that should not be added to the log file but not be visible on the console")
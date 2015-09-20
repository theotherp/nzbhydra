import logging
import unittest

class LoggingCaptor(logging.StreamHandler):
    def __init__(self):
        logging.StreamHandler.__init__(self)
        self.records = []
        
    
    def emit(self, record):
        self.records.append(record)

class MyTestCase(unittest.TestCase):
    def testThatSensitiveDataIsRemoved(self):
        from config import cfg
        
        cfg.section("main")["apikey"] = "testapikey"
        cfg.section("main")["username"] = "asecretusername"
        cfg.section("main")["password"] = "somepassword"
        
        from log import setup_custom_logger
        logger = setup_custom_logger("test")
        logging_captor = LoggingCaptor()
        logger.addHandler(logging_captor)
        
        logger.info("Test")
        logger.info("Using apikey testapikey")
        logger.info("Configured username is asecretusername")
        logger.info("somepassword")
        
        
        self.assertEqual(logging_captor.records[0].message, "Test")
        self.assertEqual(logging_captor.records[1].message, "Using apikey <XXX>")
        self.assertEqual(logging_captor.records[2].message, "Configured username is <XXX>")
        self.assertEqual(logging_captor.records[3].message, "<XXX>")
        
        logger.error("An error that should be visible on the console")
        logger.info("A text that should not be added to the log file but not be visible on the console")
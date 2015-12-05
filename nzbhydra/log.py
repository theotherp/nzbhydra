from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import re
from nzbhydra import config
from nzbhydra.config import MainSettings, mainSettings


class SensitiveDataFilter(logging.Filter):
    regex = re.compile(r"apikey=[\w]+", re.I)
    
    def filter(self, record):
        msg = record.msg
        if isinstance(msg, str):
            msg = self.regex.sub("apikey=<APIKEY>", msg)
        record.msg = msg
        return True
        

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(mainSettings.logging.consolelevel.get())
    stream_handler.setFormatter(formatter)
    
    file_handler = TimedRotatingFileHandler(filename=mainSettings.logging.logfilename.get(), when='D', interval=7)
    file_handler.setLevel(mainSettings.logging.logfilelevel.get())
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    logger.setLevel("DEBUG")
    
    logger.addFilter(SensitiveDataFilter())
    
    logging.getLogger("requests").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

    
    return logger

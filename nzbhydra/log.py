from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import cgi
import types

from future import standard_library
standard_library.install_aliases()
from builtins import *
import logging
from logging.handlers import RotatingFileHandler
import sys
import re
from os import listdir
from os.path import isfile, join, exists, getmtime
from nzbhydra import config
from nzbhydra.config import MainSettings, mainSettings

regexApikey = re.compile(r"(apikey|api)(=|:)[\w]+", re.I)
regexApikeyRepr = re.compile(r"u'(apikey|api)': u'[\w]+'", re.I)
regexUser = re.compile(r"(user|username)=[\w]+", re.I)
regexPassword = re.compile(r"(password)=[\w]+", re.I)

logger = None


def removeSensitiveData(msg):
    msg = regexApikey.sub("apikey=<APIKEY>", msg)
    msg = regexApikeyRepr.sub("'apikey':<APIKEY>'", msg)
    msg = regexUser.sub("\g<1>=<USER>", msg)
    msg = regexPassword.sub("password=<PASSWORD>", msg)
    return msg


class SensitiveDataFilter(logging.Filter):

    def filter(self, record):
        msg = record.msg
        if type(msg) is types.StringType or isinstance(msg, str):
            msg = removeSensitiveData(msg)
        record.msg = msg
        return True

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(mainSettings.logging.consolelevel.get())
    stream_handler.setFormatter(formatter)
    
    file_handler = RotatingFileHandler(filename=mainSettings.logging.logfilename.get(), maxBytes=1000000, backupCount=25)
    file_handler.setLevel(mainSettings.logging.logfilelevel.get())
    file_handler.setFormatter(formatter)

    global logger
    logger = logging.getLogger(name)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    logger.setLevel("DEBUG")
    
    logger.addFilter(SensitiveDataFilter())
    
    logging.getLogger("requests").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

    
    
    return logger

def getLogs():
    logRe = re.compile(r".*\.log(\.\d+)?")
    logFiles = [f for f in listdir(".") if isfile(f) and logRe.match(f)]
    logFiles = [{"name": f, "lastModified": getmtime(f)} for f in logFiles]
    logfile = config.mainSettings.logging.logfilename.get()
    if exists(logfile):
        logger.debug("Reading log file %s" % logfile)
        with open(logfile, "r") as logFile:
            log = cgi.escape(logFile.read())
    else:
        logger.debug("Configured log file %s was not found" % logfile)
        log = "No log available"
    return {"logFiles": logFiles, "log": log}
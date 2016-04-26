from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import cgi
import codecs
import hashlib
import types

from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
from logging.handlers import RotatingFileHandler
import sys
import re
from os import listdir
from os.path import isfile, join, exists, getmtime
from nzbhydra import config

regexApikey = re.compile(r"(apikey|api)(=|:)[\w]+", re.I)
regexApikeyRepr = re.compile(r"u'(apikey|api)': u'[\w]+'", re.I)
regexUser = re.compile(r"(user|username)=[\w]+", re.I)
regexPassword = re.compile(r"(password)=[\w]+", re.I)

# module variables
log_format = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
logger = None
logger_default_consolehandler = None

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

"""
    create a default logger so we can log prior to importing app modules or reading settings
"""
def create_logger(name='root'):
    logger_default_consolehandler = _sh = logging.StreamHandler(sys.stdout)
    _sh.setLevel('INFO')
    _sh.setFormatter(log_format)

    _logger = logging.getLogger(name)

    if not sys.executable.endswith("pythonw.exe"): #Don't use console logging if started headless
        _logger.addHandler(_sh)
    return _logger


"""
    get the root logger if created otherwise create
"""
def get_logger(name='root'):
    if name == 'root':
        global logger
        if type(logger) != logging.Logger:
            logger = create_logger()
            return logger
    return logging.getLogger(name)

# module variable
logger = create_logger()


"""
    second phase of log creation - after settings read apply them
"""
def setup_custom_logger(name, logfile=None):
    file_handler = RotatingFileHandler(filename=config.settings.main.logging.logfilename if logfile is None else logfile, maxBytes=1000000, backupCount=25)
    file_handler.setLevel(config.settings.main.logging.logfilelevel)
    file_handler.setFormatter(log_format)

    logger = get_logger(name)
    logger.addHandler(file_handler)

    # change the default console log handler level if it is not default in config
    if config.settings.main.logging.consolelevel.upper() != 'INFO':
        logger.handlers[logger_default_consolehandler].setLevel(config.settings.main.logging.consolelevel.upper())

    logger.setLevel("DEBUG")
    logger.addFilter(SensitiveDataFilter())

    logging.getLogger("requests").setLevel(logging.CRITICAL)
    logging.getLogger("urllib3").setLevel(logging.CRITICAL)
    logging.getLogger('werkzeug').setLevel(logging.CRITICAL)

    return logger


def getLogFile():
    logfile = config.settings.main.logging.logfilename
    log = None
    if exists(logfile):
        logger.debug("Reading log file %s" % logfile)
        with codecs.open(logfile, "r", 'utf-8') as logFile:
            log = cgi.escape(logFile.read())
    return log


def getAnonymizedLogFile(hideThese):
    log = getLogFile()
    if log is None:
        return None
    for hideThis in hideThese:
        if hideThis[1]:
            obfuscated = hashlib.md5(hideThis[1]).hexdigest()
            log = log.replace(hideThis[1], "<%s:%s>" % (hideThis[0], obfuscated))
    return log


def getLogs():
    logRe = re.compile(r".*\.log(\.\d+)?")
    logFiles = [f for f in listdir(".") if isfile(f) and logRe.match(f)]
    logFiles = [{"name": f, "lastModified": getmtime(f)} for f in logFiles]
    log = getLogFile()
    if log is None:
        log = "No log file found"
    return {"logFiles": logFiles, "log": log}
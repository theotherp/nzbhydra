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
LOGGER_DEFAULT_FORMAT = '%(asctime)s - %(levelname)s - %(module)s - %(message)s'
LOGGER_DEFAULT_LEVEL = 'INFO'
NOTICE_LOG_LEVEL = 25

# add custom NOTICE log level that sits between INFO and WARNING
logging.addLevelName(NOTICE_LOG_LEVEL, "NOTICE")
logging.NOTICE = NOTICE_LOG_LEVEL
def notice(self, message, *args, **kws):
    # Yes, logger takes its '*args' as 'args'.
    if self.isEnabledFor(NOTICE_LOG_LEVEL):
        self._log(NOTICE_LOG_LEVEL, message, args, **kws)
logging.Logger.notice = notice

# default root logger
logger = logging.getLogger('root')

console_logger = logging.StreamHandler(sys.stdout)
console_logger.setFormatter(logging.Formatter(LOGGER_DEFAULT_FORMAT))
console_logger.setLevel(LOGGER_DEFAULT_LEVEL)
logger.addHandler(console_logger)

logger.setLevel(LOGGER_DEFAULT_LEVEL)

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

def setup_custom_logger(name, logfile=None):
    console_log_level = config.settings.main.logging.consolelevel.upper()
    file_log_level = config.settings.main.logging.logfilelevel.upper()
    # set console log level from config file
    console_logger.setLevel(console_log_level)
    logger.setLevel(console_log_level)
    # add log file handler
    file_logger = RotatingFileHandler(filename=config.settings.main.logging.logfilename if logfile is None else logfile, maxBytes=1000000, backupCount=25)
    file_logger.setFormatter(logging.Formatter(LOGGER_DEFAULT_FORMAT))
    file_logger.setLevel(file_log_level)
    logger.addHandler(file_logger)
    # we need to set the global log level to the lowest defined
    if getattr(logging, file_log_level) < getattr(logging, console_log_level):
        logger.setLevel(file_log_level)
    # add sensitive data filter
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
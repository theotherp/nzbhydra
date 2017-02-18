# coding=utf-8
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import

import cgi
import codecs
import hashlib
import os
import tempfile
import types

from future import standard_library
#standard_library.install_aliases()
from builtins import *
import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
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
LOGGER_DEFAULT_FORMAT = u'%(asctime)s - %(levelname)s - %(module)s - %(threadName)s - %(message)s'
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

logfilename = None

console_logger = logging.StreamHandler(sys.stdout)
console_logger.setFormatter(logging.Formatter(LOGGER_DEFAULT_FORMAT))
console_logger.setLevel(LOGGER_DEFAULT_LEVEL)
logger.addHandler(console_logger)

logger.setLevel(LOGGER_DEFAULT_LEVEL)


def quiet_output():
    console_logger.setLevel(logging.CRITICAL + 1)
    # logger.removeHandler(console_logger)


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


def setup_custom_logger(logfile=None, quiet=False):
    global logfilename
    maxBytes = config.settings.main.logging.logMaxSize * 1024
    rotateAfterDays = config.settings.main.logging.logRotateAfterDays
    backupCount = config.settings.main.logging.keepLogFiles
    logfileMessage = None
    if logfile is None:
        logfilename = config.settings.main.logging.logfilename
    else:
        logfilename = logfile
        logfileMessage = "Logging to file %s as defined in the command line" % logfilename
    console_log_level = config.settings.main.logging.consolelevel.upper()
    file_log_level = config.settings.main.logging.logfilelevel.upper()
    # set console log level from config file
    if not quiet:
        console_logger.setLevel(console_log_level)
    logger.setLevel(console_log_level)
    # add log file handler
    if rotateAfterDays is None:
        file_logger = RotatingFileHandler(filename=logfilename, maxBytes=maxBytes, backupCount=backupCount)
    else:
        file_logger = TimedRotatingFileHandler(filename=logfilename, when="d", interval=rotateAfterDays, backupCount=backupCount)
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
    logger.info(logfileMessage)
    if not config.settings.main.isFirstStart and config.settings.main.logging.rolloverAtStart:
        logger.info("Starting new log file as configured")
        file_logger.doRollover()
    return logger


def getLogFile():
    global logfilename
    log = None
    if exists(logfilename):
        logger.debug("Reading log file %s" % logfilename)
        with codecs.open(logfilename, "r", 'utf-8') as logFile:
            log = cgi.escape(logFile.read())
    return log


def truncateLogFile():
    global logfilename
    logger.warn("Truncating log file %s" % logfilename)
    with open(logfilename, "w") as f:
        f.write("")
    for i in range(1,25):
        rotatedFilename = "%s.%d" % (logfilename, i)
        if os.path.exists(rotatedFilename):
            logger.info("Deleting rotated file %s" % rotatedFilename)
            os.unlink(rotatedFilename)


def getAnonymizedLogFile(hideThese, filename):
    global logfilename
    if exists(logfilename):
        logger.debug("Reading and anonymizing log file %s. This may take some time for big files..." % logfilename)
        with codecs.open(filename, "w", "utf-8") as tempFile:
            with codecs.open(logfilename, "r", 'utf-8') as logFile:
                for line in logFile:
                    line = cgi.escape(line)
                    for hideThis in hideThese:
                        if hideThis[1]:
                            obfuscated = hashlib.md5(hideThis[1]).hexdigest()
                            line = line.replace(hideThis[1], "<%s:%s>" % (hideThis[0], obfuscated))
                    tempFile.write(line + "\n")


def getLogs():
    logRe = re.compile(r".*\.log(\.\d+)?")
    logFiles = [f for f in listdir(".") if isfile(f) and logRe.match(f)]
    logFiles = [{"name": f, "lastModified": getmtime(f)} for f in logFiles]
    log = getLogFile()
    if log is None:
        log = "No log file found"
    return {"logFiles": logFiles, "log": log}
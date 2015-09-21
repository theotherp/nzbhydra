import logging
from logging.handlers import TimedRotatingFileHandler
import sys
import config

config.init("main.logging.logfile", "nzbhydra.log", str)
config.init("main.logging.logfile.level", "INFO", str)
config.init("main.logging.consolelevel", "ERROR", str)

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        #TODO: Make this easier to retrieve, what if we forget a setting somewhere? Perhaps centralize all config setting and getting in config.py and specify if a setting is sensitive 
        sensitive_strings = []
        for section in config.cfg["search_providers"].values():
            if "apikey" in section:
                sensitive_strings.append(section["apikey"])
            if "username" in section:
                sensitive_strings.append(section["username"])
            if "password" in section:
                sensitive_strings.append(section["password"])
            
        sensitive_strings.append(config.cfg["main"]["apikey"])
        sensitive_strings.append(config.cfg["main"]["username"])
        sensitive_strings.append(config.cfg["main"]["password"])
        
        
        msg = record.msg
        for sensitive_string in sensitive_strings:
            if sensitive_string is not None:
                msg = msg.replace(sensitive_string, "<XXX>")
        
        record.msg = msg
        return True
        

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(config.cfg["main"]["logging.consolelevel"])
    stream_handler.setFormatter(formatter)
    
    file_handler = TimedRotatingFileHandler(filename=config.cfg["main"]["logging.logfile"], when='D', interval=7)
    file_handler.setLevel(config.cfg["main"]["logging.logfile.level"])
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    logger.setLevel("DEBUG")
    
    logger.addFilter(SensitiveDataFilter())
    
    return logger

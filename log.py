import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from config import init, get_config

init("main.logging.logfile", "nzbhydra.log", str)
init("main.logging.logfile.level", "INFO", str)
init("main.logging.consolelevel", "ERROR", str)

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        #TODO: Make this easier to retrieve, what if we forget a setting somewhere? Perhaps centralize all config setting and getting in config.py and specify if a setting is sensitive 
        sensitive_strings = []
        for section in get_config().section("search_providers").sections():
            sensitive_strings.append(section.get("apikey"))
            sensitive_strings.append(section.get("username"))
            sensitive_strings.append(section.get("password"))
            
        sensitive_strings.append(get_config().section("main").get("apikey"))
        sensitive_strings.append(get_config().section("main").get("username"))
        sensitive_strings.append(get_config().section("main").get("password"))
        
        msg = record.msg
        for sensitive_string in sensitive_strings:
            if sensitive_string is not None:
                msg = msg.replace(sensitive_string, "<XXX>")
        
        record.msg = msg
        return True
        

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(get_config()["main.logging.consolelevel"])
    stream_handler.setFormatter(formatter)
    
    file_handler = TimedRotatingFileHandler(filename=get_config()["main.logging.logfile"], when='D', interval=7)
    file_handler.setLevel(get_config()["main.logging.logfile.level"])
    file_handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    
    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    logger.setLevel("DEBUG")
    
    logger.addFilter(SensitiveDataFilter())
    
    return logger

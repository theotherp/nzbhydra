import logging
from logging.handlers import TimedRotatingFileHandler
import sys
from nzbhydra import config
from nzbhydra.config import MainSettings, mainSettings


class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
         
        sensitive_strings = []
        #todo:
        # for section in config.cfg.section("search_providers").sections():
        #     sensitive_strings.append(section.get("apikey"))
        #     sensitive_strings.append(section.get("username"))
        #     sensitive_strings.append(section.get("password"))
            
        sensitive_strings.append(config.get(mainSettings.username))
        sensitive_strings.append(config.get(mainSettings.password))
        sensitive_strings.append(config.get(mainSettings.apikey))
        
        msg = record.msg
        for sensitive_string in sensitive_strings:
            if sensitive_string is not None and sensitive_string != "":
                msg = msg.replace(sensitive_string, "<XXX>")
        
        record.msg = msg
        return True
        

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(config.get(mainSettings.consolelevel))
    stream_handler.setFormatter(formatter)
    
    file_handler = TimedRotatingFileHandler(filename=config.get(mainSettings.logfile), when='D', interval=7)
    file_handler.setLevel(config.get(mainSettings.logfilelevel))
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

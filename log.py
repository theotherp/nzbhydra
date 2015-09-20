import logging
from config import cfg

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        #TODO: Make this easier to retrieve, what if we forget a setting somewhere? Perhaps centralize all config setting and getting in config.py and specify if a setting is sensitive 
        sensitive_strings = []
        for section in cfg.section("search_providers").sections():
            sensitive_strings.append(section.get("apikey"))
            sensitive_strings.append(section.get("username"))
            sensitive_strings.append(section.get("password"))
            
        sensitive_strings.append(cfg.section("main").get("apikey"))
        sensitive_strings.append(cfg.section("main").get("username"))
        sensitive_strings.append(cfg.section("main").get("password"))
        
        msg = record.msg
        for sensitive_string in sensitive_strings:
            if sensitive_string is not None:
                msg = msg.replace(sensitive_string, "<XXX>")
        
        record.msg = msg
        return True
        

def setup_custom_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s - %(levelname)s - %(module)s - %(message)s')

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    
    logger.addFilter(SensitiveDataFilter())
    
    return logger

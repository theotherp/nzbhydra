import os
from os.path import dirname, join, abspath
from sys import path
base_path = dirname(abspath(__file__))
path.insert(0, join(base_path, 'nzbhydra'))
path.insert(0, join(base_path, 'libs'))

import argparse
import requests
import nzbhydra.config as config
from nzbhydra import log
from nzbhydra import indexers
from nzbhydra import database
from nzbhydra import web

requests.packages.urllib3.disable_warnings()
logger = None

def run():
    global logger
    parser = argparse.ArgumentParser(description='NZBHydra')
    parser.add_argument('--config', action='store', help='Settings file to load', default="settings.cfg")
    parser.add_argument('--database', action='store', help='Database file to load', default="nzbhydra.db")
    parser.add_argument('--host', action='store', help='Host to run on')
    parser.add_argument('--port', action='store', help='Port to run on', type=int)
    args = parser.parse_args()
    
    settings_file = args.config
    database_file = args.database
    
    print("Loading settings from %s" % settings_file)
    config.load(settings_file)
    config.save(settings_file) #Write any new settings back to the file
    logger = log.setup_custom_logger('root')
    logger.info("Started")
    logger.info("Loading database file %s" % database_file)
    if not os.path.exists(database_file):
        database.init_db(database_file)
    database.db.init(database_file)
    indexers.read_indexers_from_config()

    host = config.mainSettings.host.get() if args.host is None else args.host
    port = config.mainSettings.port.get() if args.port is None else args.port
    
    if config.mainSettings.debug.get():
        logger.info("Debug mode enabled")
    logger.info("Starting web app on %s:%d" % (host, port))
    web.run(host, port)


if __name__ == '__main__':
    run()

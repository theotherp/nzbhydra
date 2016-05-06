from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from builtins import range
from future import standard_library

from peewee import fn

#standard_library.install_aliases()
from builtins import *
import logging
from nzbhydra import config, database
from nzbhydra.database import Indexer
from nzbhydra.searchmodules import newznab, womble, nzbclub, nzbindex, binsearch, omgwtf #Actually used but referenced dynamically

logger = logging.getLogger('root')
configured_indexers = []
enabled_indexers = []


def init_indexer_table_entry(indexer_name):
    try:
        Indexer.get(fn.lower(Indexer.name) == indexer_name.lower())
    except Indexer.DoesNotExist as e:
        logger.info("Unable to find indexer with name %s in database. Will add it" % indexer_name)
        Indexer().create(name=indexer_name)


# Load from config and initialize all configured indexers using the loaded modules
def read_indexers_from_config():
    database.db.connect()
    global enabled_indexers, configured_indexers
    enabled_indexers = []

    for indexer in config.settings.indexers:
        try:
            instance = sys.modules["nzbhydra.searchmodules." + indexer.type].get_instance(indexer)
        except Exception:
            if hasattr(indexer, "type"): 
                logger.error("Unable to get reference to search module %s" % indexer.type)
            else:
                logger.error("%s has no type setting" % indexer)
            continue
        logger.debug("Found indexer %s" % instance.name)
        init_indexer_table_entry(instance.name)
        configured_indexers.append(instance)
        if indexer.enabled:
            enabled_indexers.append(instance)
            logger.info("Activated indexer %s" % instance.name)
        
                  
    database.db.close()            
    return enabled_indexers


def getIndexerByName(name):
    for i in enabled_indexers:
        if i.name == name:
            return i
    return None


def getIndexerSettingByName(name):
    for i in config.settings.indexers:
        if i.name == name:
            return i
    return None


def clean_up_database():
    configured_indexer_names = set([x.name for x in configured_indexers])
    for indexer in database.Indexer.select():
        if indexer.name not in configured_indexer_names:
            logger.info("Removing old indexer entry %s from database" % indexer.name)
            indexer.delete_instance()
        
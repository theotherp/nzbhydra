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
from nzbhydra.searchmodules import newznab, womble, nzbclub, nzbindex, binsearch, omgwtf

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

    instance = binsearch.get_instance(config.indexerSettings.binsearch)
    if config.indexerSettings.binsearch.enabled.get():
        enabled_indexers.append(instance)
        logger.info("Loading indexer %s" % instance.name)
    init_indexer_table_entry(instance.name)
    configured_indexers.append(instance)
    
    instance = nzbindex.get_instance(config.indexerSettings.nzbindex)
    if config.indexerSettings.nzbindex.enabled.get():
        enabled_indexers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
    init_indexer_table_entry(instance.name)
    configured_indexers.append(instance)
        
    instance = nzbclub.get_instance(config.indexerSettings.nzbclub)
    if config.indexerSettings.nzbclub.enabled.get():
        enabled_indexers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
    init_indexer_table_entry(instance.name)
    configured_indexers.append(instance)

    instance = omgwtf.get_instance(config.indexerSettings.omgwtf)
    if config.indexerSettings.omgwtf.enabled.get():
        enabled_indexers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
    init_indexer_table_entry(instance.name)
    configured_indexers.append(instance)
        
    instance = womble.get_instance(config.indexerSettings.womble)
    if config.indexerSettings.womble.enabled.get():
        enabled_indexers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
    init_indexer_table_entry(instance.name)
    configured_indexers.append(instance)
        
    for i in range(1, 41):
        newznabsetting = config.get_newznab_setting_by_id(i)
        if newznabsetting.name.get() is not None and newznabsetting.name.get() != "": 
            instance = newznab.get_instance(newznabsetting)
            if newznabsetting.enabled.get():
                enabled_indexers.append(instance)
                logger.info("Loaded indexer %s" % instance.name)
            init_indexer_table_entry(instance.name)
            configured_indexers.append(instance)
        else:
            logger.debug("Skipping newznab indexer #%d because it has no name" % i)
        
                  
    database.db.close()            
    return enabled_indexers


def getIndexerByName(name):
    for i in enabled_indexers:
        if i.name == name:
            return i
    return None


def clean_up_database():
    configured_indexer_names = set([x.name for x in configured_indexers])
    for indexer in database.Indexer.select():
        if indexer.name not in configured_indexer_names:
            logger.info("Removing old indexer entry %s from database" % indexer.name)
            indexer.delete_instance()
        
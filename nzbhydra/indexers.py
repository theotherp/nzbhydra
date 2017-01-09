from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import logging

from builtins import *
from peewee import fn

from nzbhydra import config, database
from nzbhydra.database import Indexer, IndexerStatus
from nzbhydra.exceptions import IndexerNotFoundException
from nzbhydra.searchmodules import anizb, binsearch, jackett, newznab, nzbclub, nzbindex

logger = logging.getLogger('root')
configured_indexers = []
enabled_indexers = []


def init_indexer_table_entry(indexer_name):
    try:
        Indexer.get(fn.lower(Indexer.name) == indexer_name.lower())
    except Indexer.DoesNotExist as e:
        logger.info("Unable to find indexer with name %s in database. Will add it" % indexer_name)
        indexer = Indexer().create(name=indexer_name)
        IndexerStatus.create_or_get(indexer=indexer, first_failure=None, latest_failure=None, disabled_until=None)


# Load from config and initialize all configured indexers using the loaded modules
def read_indexers_from_config():
    global enabled_indexers, configured_indexers
    enabled_indexers = []
    configured_indexers = []

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

    return enabled_indexers


def getIndexerByName(name):
    for i in configured_indexers:
        if i.name == name:
            return i
    raise IndexerNotFoundException("Unable to find indexer named %s" % name)


def getIndexerSettingByName(name):
    for i in config.settings.indexers:
        if i.name == name:
            return i
    return None


def getIndexerSettingByType(itype):
    for i in config.settings.indexers:
        if i.type == itype:
            return i
    return None


def clean_up_database():
    configured_indexer_names = set([x.name for x in configured_indexers])
    for indexer in database.Indexer.select():
        if indexer.name not in configured_indexer_names:
            logger.info("Removing old indexer entry %s from database" % indexer.name)
            indexer.delete_instance()

import logging

from nzbhydra import config
from nzbhydra.config import providerBinsearchSettings
from nzbhydra.database import Provider
from nzbhydra.searchmodules import newznab, womble, nzbclub, nzbindex, binsearch


# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase. Realistically there won't be any plugins anyway... At least none written by me which need code change
search_modules = {"newznab": newznab, "womble": womble, "nzbclub": nzbclub, "nzbindex": nzbindex, "binsearch": binsearch}
providers = []

logger = logging.getLogger('root')


# Load from config and initialize all configured providers using the loaded modules
def read_providers_from_config():
    global providers
    providers = []

    if config.providerBinsearchSettings.enabled.get():
        instance = binsearch.get_instance(providerBinsearchSettings)
        providers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
        
    if config.providerNzbindexSettings.enabled.get():
        instance = nzbindex.get_instance(config.providerNzbindexSettings)
        providers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
        
    if config.providerNzbclubSettings.enabled.get():
        instance = nzbclub.get_instance(config.providerNzbclubSettings)
        providers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
        
    if config.providerWombleSettings.enabled.get():
        instance = womble.get_instance(config.providerWombleSettings)
        providers.append(instance)
        logger.info("Loaded indexer %s" % instance.name)
        
    for i in range(1, 8):
        newznabsetting = config.get_newznab_setting_by_id(i)
        if newznabsetting.enabled.get():
            instance = newznab.get_instance(newznabsetting)
            try:
                instance.provider.name
                providers.append(instance)
                logger.info("Loaded indexer %s" % instance.name)
            except Provider.DoesNotExist as e:
                logger.error("Unable to find provider with name %s in database" % instance.name)
                
                
            
        
    

    return providers

from nzbhydra import config
from nzbhydra.config import ProviderBinsearchSettings
from nzbhydra.database import Provider
from nzbhydra.searchmodules import newznab, womble, nzbclub, nzbindex, binsearch

# TODO: I would like to use plugins for this but couldn't get this to work with pluginbase. Realistically there won't be any plugins anyway... At least none written by me which need code change
search_modules = {"newznab": newznab, "womble": womble, "nzbclub": nzbclub, "nzbindex": nzbindex, "binsearch": binsearch}
providers = []


# Load from config and initialize all configured providers using the loaded modules
def read_providers_from_config():
    global providers
    providers = []
    
    if config.providerBinsearchSettings.enabled.get():
        providers.append(binsearch.get_instance(ProviderBinsearchSettings()))
        
    return providers

from collections import namedtuple
from enum import Enum, EnumMeta
import profig

cfg = profig.Config()


def load(filename):
    global cfg
    cfg.read(filename)
    # Manually set the source to this settings file so that when syncing the settings are written back. If we don't do this it loads the settings but doesn't write them back. Or we would need to store the
    # settings filename and call write(filename)
    cfg.sources = [filename]
    cfg.sync()


def init(path, value, type, comment=None):
    global cfg
    cfg.init(path, value, type, comment)
    # Write this to console for now, later we can use it to collect all available/expected config data


def get(setting, section=None, default=None):
    parent = cfg.section(section) if section is not None else cfg
    return parent.get(setting.name, default=default if default is not None else setting.default)


def set(setting, value, section=None):
    parent = cfg.section(section) if section is not None else cfg
    parent[setting.name] = value


class InitSettings(object):
    def __init__(self, setting_class):
        # Somewhat hacky, but it works. We take all of the non-builtin attributes (the subsettings) of the section class and set them to our decorator class.
        # We also initialize them in profig (which is what we want to achieve)
        for d in dir(setting_class):
            if not d.startswith("__"):
                setting = getattr(setting_class, d)
                if isinstance(setting, Setting):
                    print("Initializing configuration. Name: %s. Default: %s. Type: %s. Comment: %s" % (setting.name, setting.default, setting.type, setting.comment))
                    cfg.init(setting.name, setting.default, setting.type, setting.comment)
                    setattr(self, d, setting)
                elif isinstance(setting, EnumMeta):
                    setattr(self, d, setting)
                


Setting = namedtuple("Setting", "name default type options comment")


def setting(name, default, type=None, options=[], comment=None):
    return Setting(name=name, default=default, type=type, options=options, comment=comment)


def get2(setting: Setting):
    return cfg.get(setting.name, setting.default)

@InitSettings
class MainSettings(object):
    host = setting(name="main.host", default="127.0.0.1", type=str)
    port = setting(name="main.port", default=5050, type=int)
    logfile = setting(name="main.logging.logfile", default="nzbhydra.log", type=str)
    logfilelevel = setting(name="main.logging.logfile.level", default="INFO", type=str)
    consolelevel = setting(name="main.logging.consolelevel", default="ERROR", type=str)
    username = setting(name="main.username", default="", type=str)
    password = setting(name="main.password", default="", type=str)
    apikey = setting(name="main.apikey", default="", type=str)
    enable_auth = setting(name="main.enableAuth", default="", type=bool)
    
@InitSettings
class ResultProcessing(object):
    duplicateSizeThresholdInPercent = setting(name="resultProcessing.duplicateSizeThresholdInPercent", default=0.1, type=float)
    duplicateAgeThreshold = setting(name="resultProcessing.duplicateAgeThreshold", default=3600, type=int)
     
   
@InitSettings
class SearchingSettings(object):
    timeout = setting(name="searching.timeout", default=5, type=int)
    ignoreTemporarilyDisabled = setting(name="searching.ignoreTemporarilyDisabled", default=False, type=bool)   
    allowQueryGeneration = setting(name="searching.allowQueryGeneration", default="both", type=str)
 
@InitSettings
class SabnzbdSettings(object):
    host = setting(name="downloader.sabnzbd.host", default="127.0.0.1", type=str)
    port = setting(name="downloader.sabnzbd.port", default=8086, type=int)
    

@InitSettings
class DownloaderSettings(object):
    
    class NzbAccessTypeOptions(Enum):
        serve = "serve"
        redirect = "redirect"
        direct = "direct"
        
    class NzbAddingTypeOptions(Enum):
        link = "link"
        nzb = "nzb"
    
    nzbaccesstype = setting(name="downloader.nzbaccesstype", default="serve", type=str, comment="Determines how we provide access to NZBs  ""Serve"": Provide a link to NZBHydra via which the NZB is downloaded and returned. ""Redirect"": Provide a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links (as returned by the provider=. Not recommended.")
    nzbAddingType = setting(name="downloader.nzbAddingType", default="link", type=str, comment="Determines how NZBs are added to downloaders. Either by sending a link to the downloader (""link"") or by sending the actual NZB (""nzb"").")




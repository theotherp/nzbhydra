import profig

cfg = profig.Config()


def load(filename):
    global cfg
    cfg.read(filename)
    # Manually set the source to this settings file so that when syncing the settings are written back. If we don't do this it loads the settings but doesn't write them back. Or we would need to store the
    # settings filename and call write(filename)
    cfg.sources = [filename]


def init(path, value, type, comment=None):
    global cfg
    cfg.init(path, value, type, comment)
    # Write this to console for now, later we can use it to collect all available/expected config data


# The following classes allow us to access settings using indexed values instead of strings. They are initialized at startup with a decorator and added to profig.
# We can access them using e.g.
#    get(Host)
# We can also add possible values for comparison, e.g. for DownloaderAddtype:
#   get(DownloaderAddtype) == DownloaderAddtype.redirect -> bool


def get(setting, default=None):
    return cfg.get(setting.setting, default=default if default is not None else setting.default)


class InitSettings(object):
    def __init__(self, setting_class):
        # Somewhat hacky, but it works. We take all of the non-builtin attributes of the setting class and set them to our class
        for d in dir(setting_class):
            if not d.startswith("__"):
                setattr(self, d, getattr(setting_class, d))
        self.comment = setting_class.comment if hasattr(setting_class, "comment") else None
        print("Initializing configuration with path %s and value %s and comment %s" % (setting_class.setting, setting_class.default, self.comment))
        cfg.init(setting_class.setting, setting_class.default, setting_class.type, self.comment)


# Main settings

@InitSettings
class Host(object):
    setting = "main.host"
    default = "127.0.0.1"
    type = str


@InitSettings
class Port(object):
    setting = "main.port"
    default = 5050
    type = int


@InitSettings
class Logfile(object):
    setting = "main.logging.logfile"
    default = "nzbhydra.log"
    type = str


@InitSettings
class LogfileLevel(object):
    setting = "main.logging.logfile.level"
    default = "INFO"
    type = str


@InitSettings
class ConsoleLevel(object):
    setting = "main.logging.consolelevel"
    default = "ERROR"
    type = str


@InitSettings
class Username(object):
    setting = "main.username"
    default = "nzbhydra"
    type = str


@InitSettings
class Password(object):
    setting = "main.password"
    default = "nzbhydra"
    type = str


@InitSettings
class Apikey(object):
    setting = "main.apikey"
    default = "nzbhydra"
    type = str


@InitSettings
class EnableAuth(object):
    setting = "main.auth"
    default = False
    type = bool


# Result processing settings

@InitSettings
class DuplicateSizeThreshold(object):
    setting = "ResultProcessing.duplicateSizeThresholdInPercent"
    default = 0.1
    type = float


@InitSettings
class DuplicateAgeThreshold(object):
    setting = "ResultProcessing.duplicateAgeThreshold"
    default = 3600
    type = int


# Searching settings

@InitSettings
class SearchingTimeout(object):
    setting = "searching.timeout"
    default = 5
    type = int


@InitSettings
class IgnoreTemporarilyDisabled(object):
    setting = "searching.ignore_temporarily_disabled"
    default = False
    type = bool


@InitSettings
class AllowQueryGeneration(object):
    setting = "searching.allow_query_generation"
    default = "both"
    type = str


# Downloader settings

@InitSettings
class DownloaderAddtype(object):
    setting = "downloader.addtype"
    default = "serve"
    type = str
    comment = "Determines how we internally handle NZBs (accessed via the GUI, not the API). ""Serve"": Download the NZB from the provider and send it to the downloader (preferred). ""Redirect"": Send a link to NZBHydra which redirects to the provider. ""Direct"": Create direct links. Not recommended."

    serve = "serve"
    redirect = "redirect"
    direct = "direct"



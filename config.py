import configobj
from configobj import ConfigObj
cfg = ConfigObj('settings.cfg')
#cfg.sync()

inits = []


def init(path, value, type):
    #cfg.init(path, value, type)
    #Store the init in case the config file is reloaded. I guess the whole handling should be done differently, but this is what I came up with...
    #inits.append({"path": path, "value": value, "type": type})
    #We cannot use logging because this is executed before the logger was initialized and configured
    print("Initializing configuration with path %s and value %s" % (path, value))


#We load the config from the given filename and re-init all the settings that were initialized before so the types are kept
def reload(filename):
    global cfg
    print("Reloading config from %s" % filename)
    cfg = ConfigObj(filename)
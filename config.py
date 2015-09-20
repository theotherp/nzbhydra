import profig

cfg = profig.Config('settings.cfg')
cfg.sync()

inits = []

def init(path, value, type):
    cfg.init(path, value, type)
    #Store the init in case the config file is reloaded. I guess the whole handling should be done differently, but this is what I came up with...
    inits.append({"path": path, "value": value, "type": type})
    #We cannot use logging because this is executed before the logger was initialized and configured
    print("Initializing configuration with path %s and value %s" % (path, value))

#We load the config from the given filename and re-init all the settings that were initialized before so the types are kept
def reload(filename):
    new_cfg = profig.Config(filename)
    new_cfg.sync()
    for i in inits:
        new_cfg.init(i["path"], i["value"], i["type"])
    return new_cfg
    #cfg.read(filename)

        
import profig

cfg = profig.Config('settings.cfg')
cfg.sync()


def init(path, value, type):
    cfg.init(path, value, type)
    print("Initializing configuration with path %s and value %s" % (path, value))
import profig

cfg = profig.Config()


def load(filename):
    global cfg
    cfg.read(filename)
    cfg.sources = [filename]
inits = []


def init(path, value, type):
    global cfg
    cfg.init(path, value, type)
    print("Initializing configuration with path %s and value %s" % (path, value))

        
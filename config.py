import profig

cfg = profig.Config()


def load(filename):
    global cfg
    cfg.read(filename)
    #Manually set the source to this settings file so that when syncing the settings are written back. If we don't do this it loads the settings but doesn't write them back. Or we would need to store the
    #settings filename and call write(filename)
    cfg.sources = [filename]


def init(path, value, type):
    global cfg
    cfg.init(path, value, type)
    #Write this to console for now, later we can use it to collect all available/expected config data
    print("Initializing configuration with path %s and value %s" % (path, value))

        
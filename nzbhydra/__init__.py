from os.path import dirname, abspath

import thread

configFile = None
databaseFile = None
databaseLock = thread.allocate_lock()

def getBasePath():
    try:
        basepath = dirname(dirname(abspath(__file__)))
    except NameError:  # We are the main py2exe script, not a module
        import sys
        basepath = dirname(abspath(sys.argv[0]))
    if "library.zip" in basepath:
        basepath = basepath[:basepath.find("library.zip")]
    return basepath
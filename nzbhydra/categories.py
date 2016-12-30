import logging

from bunch import Bunch

categories = Bunch.fromDict([{"name": 'na', "pretty": "N/A", "supportsById": False, "mayBeSelected": False, "newznabCategories": [], "applyRestrictions": False, "forbiddenWords": None, "requiredWords": None, "ignoreResults": "never", "forbiddenRegex": None, "requiredRegex": None},
                             {"name": 'all', "pretty": "All", "supportsById": False, "newznabCategories": [], "applyRestrictions": False, "forbiddenWords": None, "requiredWords": None, "mayBeSelected": True, "forbiddenRegex": None, "requiredRegex": None, "ignoreResults": False},
                             {"name": 'movies', "pretty": "Movies", "supportsById": True, "mayBeSelected": True},
                             {"name": 'movieshd', "pretty": "Movies HD", "supportsById": True, "mayBeSelected": True},
                             {"name": 'moviessd', "pretty": "Movies SD", "supportsById": True, "mayBeSelected": True},
                             {"name": 'tv', "pretty": "TV", "supportsById": True, "mayBeSelected": True},
                             {"name": 'tvhd', "pretty": "TV HD", "supportsById": True, "mayBeSelected": True},
                             {"name": 'tvsd', "pretty": "TV SD", "supportsById": True, "mayBeSelected": True},
                             {"name": 'anime', "pretty": "Anime", "supportsById": False, "mayBeSelected": True},
                             {"name": 'audio', "pretty": "Audio", "supportsById": False, "mayBeSelected": True},
                             {"name": 'flac', "pretty": "Audio FLAC", "supportsById": False, "mayBeSelected": True},
                             {"name": 'mp3', "pretty": "Audio MP3", "supportsById": False, "mayBeSelected": True},
                             {"name": 'audiobook', "pretty": "Audiobook", "supportsById": False, "mayBeSelected": True},
                             {"name": 'console', "pretty": "Console", "supportsById": False, "mayBeSelected": True},
                             {"name": 'pc', "pretty": "PC", "supportsById": False, "mayBeSelected": True},
                             {"name": 'xxx', "pretty": "XXX", "supportsById": False, "mayBeSelected": True},
                             {"name": 'ebook', "pretty": "Ebook", "supportsById": False, "mayBeSelected": True},
                             {"name": 'comic', "pretty": "Comic", "supportsById": False, "mayBeSelected": True}
                             ])

logger = logging.getLogger('root')


def getUnknownCategory():
    return getCategories()[0]


def getCategoryByName(name):
    """
    Returns the category of the given name or the "N/A" category if none is found
    :param name: 
    :return: 
    """
    cats = getCategories()
    for c in cats:
        if c["name"] == name:
            return c
    return cats[0]


def getListFromNewznabCats(cats):
    if cats is None or (isinstance(cats, list) and len(cats) == 0) or cats == "":
        return []
    if representsInt(cats):
        cats = [cats]
    if isinstance(cats, str) or isinstance(cats, unicode):
        cats = cats.split(",")
    cats = [int(x) for x in cats]
    return cats


def getByNewznabCats(cats):
    cats = getListFromNewznabCats(cats)
    cats = sorted(cats, reverse=True)  # Sort to make the most specific category appear first
    configuredCategories = getCategories()
    if len(cats) > 0:
        for cat in cats:
            for cmpCat in configuredCategories:
                if cat in cmpCat["newznabCategories"]:
                    return cmpCat
        else:
            # We did not find a category, let's try to find a more general one that fits this
            cat = cats[0] / 1000 * 1000  # e.g. 2090 -> 2000
            for cmpCat in configuredCategories:
                if cat in cmpCat["newznabCategories"]:
                    return cmpCat

    return configuredCategories[0]


def representsInt(s):
    if isinstance(s, int):
        return True
    if not isinstance(s, str) and not isinstance(s, unicode):
        return False
    try:
        int(s)
        return True
    except ValueError:
        return False


def getCategoryByAnyInput(cat):
    """
    Parses the input and returns the proper category. Should only be used for parsing of search categories.
    :param cat: 
    :return: 
    """
    if isinstance(cat, Bunch):
        return Bunch.fromDict({"type": "hydra", "category": cat})
    if isinstance(cat, list) and len(cat) == 0:
        return Bunch.fromDict({"type": "newznab", "category": getCategories()[1]})
    if not cat:
        return Bunch.fromDict({"type": "hydra", "category": getCategories()[1]})
    if isinstance(cat, list) or representsInt(cat) or "," in cat:
        category = getByNewznabCats(cat)
        if category is None:
            logger.info("Unable to find hydra category for input %s. Falling back to \"All\"" % cat)
            category = getCategories()[0]
        return Bunch.fromDict({"type": "newznab", "original": getListFromNewznabCats(cat), "category": category})
    for c in getCategories():
        if cat in [c["name"], c["pretty"]]:
            return Bunch.fromDict({"type": "hydra", "category": c})
    # Return "All" if not found
    return Bunch.fromDict({"type": "hydra", "category": getCategories()[1]})


def getCategories():
    from nzbhydra import config
    for c in categories:
        for k, v in config.settings["categories"]["categories"].items():
            if c["name"] == k:
                c.update(v)
    return categories


def getNumberOfSelectableCategories():
    return len([x for x in categories if x.mayBeSelected])


#TODO this is a lot more work than a simple newznab request
#we need to transform the search to meaningful queries (show search, movie search)
#       for this use 1x01 and s01e01 and season01 and season1 and s01 etc
#we could support experimental option "only show collections", perhaps when not using the api or never or in both cases (to configure!)

#we need to parse html
#we need to throw out all of those that we don't want in any case (how to decide this?)
from search_module import SearchModule


class Binsearch(SearchModule):
    
    def __init__(self, cfg):
        super(Binsearch, self).__init__(cfg)
        self.module_name = "Binsearch"
    
    pass


def get_instance(cfg):
    return Binsearch(cfg)
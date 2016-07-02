import unittest

from bunch import Bunch

from nzbhydra import categories, config

class TestCategories(unittest.TestCase):

    def testCategoryMerge(self):
        config.settings = Bunch.fromDict(config.initialConfig)
        cats = categories.getCategories()
        self.assertEqual(18, len(cats))
        self.assertEqual("movies", cats[2].name)
        self.assertEqual([2000], cats[2].newznabCategories)
        self.assertEqual("movieshd", cats[3].name)
        self.assertEqual([2040, 2050, 2060], cats[3].newznabCategories)
        
    def testGetByNewznabCats(self):
        config.settings = Bunch.fromDict(config.initialConfig)
        cats = "2000"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movies", result.name)

        cats = 2000
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movies", result.name)

        cats = "2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

        cats = u"2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

        cats = "2040,2050"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

        cats = "2050,2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

        cats = u"2050,2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

        cats = [2050, 2040]
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)
        
        #Test fallback to more general category
        cats = "2090"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movies", result.name)

        cats = "2080, 2090"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movies", result.name)
        
        #Don't fall back if one category matches a more specific one
        cats = "2040, 2090"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)
        
        cats = "2090, 2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)
        
        #Use the most specific category
        cats = "2000, 2040"
        result = categories.getByNewznabCats(cats)
        self.assertEqual("movieshd", result.name)

    def testGetCategoryByAnyInput(self):
        config.settings = Bunch.fromDict(config.initialConfig)
        
        cats = "2000"
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual([2000], result.original)
        self.assertEqual("movies", result.category.name)

        cats = u"2000"
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual([2000], result.original)
        self.assertEqual("movies", result.category.name)

        cats = ""
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("hydra", result.type)
        self.assertEqual("all", result.category.name)

        cats = []
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual("all", result.category.name)

        cats = None
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("hydra", result.type)
        self.assertEqual("all", result.category.name)

        cats = 2000
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual([2000], result.original)
        self.assertEqual("movies", result.category.name)

        cats = [2000, 2010]
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual([2000, 2010], result.original)
        self.assertEqual("movies", result.category.name)

        cats = ["2000", "2010"]
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("newznab", result.type)
        self.assertEqual([2000, 2010], result.original)
        self.assertEqual("movies", result.category.name)

        cats = "movies"
        result = categories.getCategoryByAnyInput(cats)
        self.assertEqual("hydra", result.type)
        self.assertEqual("movies", result.category.name)
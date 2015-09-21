from pprint import pprint
import unittest
from furl import furl
import profig
import requests
import sys
import search
import config

import logging
logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")

from searchmodules.newznab import NewzNab



class MyTestCase(unittest.TestCase):
    
    config.cfg = profig.Config()
    
    config.cfg["searching.timeout"] = 5
    
    config.cfg["search_providers.1.enabled"] = True
    config.cfg["search_providers.1.module"] = "newznab"
    config.cfg["search_providers.1.name"] = "NZBs.org"
    config.cfg["search_providers.1.apikey"] = "apikeynzbsorg"
    config.cfg["search_providers.1.base_url"] = "https://nzbs.org"
    config.cfg["search_providers.1.query_url"] = "http://127.0.0.1:5001/nzbsorg"
    config.cfg["search_providers.1.search_types"] = "general, tv, movie"
    
    config.cfg["search_providers.2.enabled"] = True
    config.cfg["search_providers.2.module"] = "newznab"
    config.cfg["search_providers.2.name"] = "DOGNzb"
    config.cfg["search_providers.2.apikey"] = "apikeydognzb"
    config.cfg["search_providers.2.base_url"] = "https://dognzb.cr"
    config.cfg["search_providers.2.query_url"] = "http://127.0.0.1:5001/dognzb"
    config.cfg["search_providers.2.search_types"] = "general, tv"
    
    config.cfg["search_providers.3.enabled"] = True
    config.cfg["search_providers.3.module"] = "womble"
    config.cfg["search_providers.3.name"] = "womble"
    config.cfg["search_providers.3.base_url"] = "http://www.newshost.co.za"
    config.cfg["search_providers.3.query_url"] = "http://www.newshost.co.za/rss"
    config.cfg["search_providers.3.search_types"] = "tv"
    config.cfg["search_providers.3.supports_queries"] = False
    
    def test_search_module_loading(self):
        self.assertEqual(3, len(search.search_modules))
        
    def test_read_providers(self):
        providers = search.read_providers_from_config()
        self.assertEqual(3, len(providers))
        
    def test_pick_providers(self):
        search.read_providers_from_config()
        providers = search.pick_providers("general")
        self.assertEqual(2, len(providers))
        
        #Providers with tv search and which support queries (actually searching for particular releases)
        providers = search.pick_providers("tv")
        self.assertEqual(2, len(providers))
        
        #Providers with tv search, including those that only provide a list of latest releases 
        providers = search.pick_providers("tv", False)
        self.assertEqual(3, len(providers))
        
        providers = search.pick_providers("movie")
        self.assertEqual(1, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)
        
    def testSearch(self):
        search.read_providers_from_config()
        results = search.search("avengers")
        assert len(results) > 190 #fuzzy...
        
        
    def testSearchResultsToDict(self):
        n = NewzNab(config.cfg)
        #nzbsorg
        with open("tests/mock/nzbsorg_q_avengers_3results.json") as f:
            entries = n.process_query_result(f.read())
        from nzbhydra import render_search_results_for_api
        from nzbhydra import app
        with app.test_request_context("/"):
            xhtml = render_search_results_for_api(entries)
    
    
    
    def getMock(self, action, category=None, rid=None, imdbid=None, season=None, episode=None, q=None):
        query = furl("https://nzbs.org/api").add({"apikey": "", "t": action, "o": "json", "extended": 1})
        if rid is not None:
            query.add({"rid": rid})
        if episode is not None:
            query.add({"ep": episode})
        if season is not None:
            query.add({"season": season})
        if imdbid is not None:
            query.add({"imdbid": imdbid})
        if q is not None:
            query.add({"q": q})
        if category is not None:
            query.add({"cat": category})
        
        print(query.tostr())
        r = requests.get(query.tostr())
        args = query.args.keys()
        args.remove("apikey")
        args.remove("o")
        args.remove("extended")
        filename = "nzbsorg"
        args = sorted(args)
        for arg in args:
            filename = "%s--%s-%s" % (filename, arg, query.args[arg])
        filename += ".json"
        pprint(args)
        print(filename)
        with open(filename, "w") as file:
            file.write(r.text)
        
        
    def testGetMockResponses(self):
        #Enable to create mock responses
        if False:
            self.getMock("search") #all
            self.getMock("search", q="avengers") #general search avengers
            self.getMock("search", q="avengers", category="2000") #general search avengers all movies
            self.getMock("search", category="5030") #all tv sd
            self.getMock("search", category="5040") #all tv hd
            
            self.getMock("tvsearch") #tvsearch all
            self.getMock("tvsearch", category="5030") #tvsearch all sd
            self.getMock("tvsearch", category="5040") #tvsearch all hd
            self.getMock("tvsearch", category="5040", rid=80379) #bbt hd
            self.getMock("tvsearch", category="5030", rid=80379) #bbt sd
            self.getMock("tvsearch", category="5040", rid=80379, season=1) #bbt hd season 1
            self.getMock("tvsearch", category="5040", rid=80379, season=1, episode=2) #bbt hd season 1 episode 2
            
            self.getMock("movie") #moviesearch all
            self.getMock("movie", category="2040") #moviesearch all hd
            self.getMock("movie", category="2030") #moviesearch all sd
            self.getMock("movie", imdbid="0169547") #moviesearch american beauty all
            self.getMock("movie", category="2040", imdbid="0169547") #moviesearch american beauty all hd
        
        
         
        
        
        


if __name__ == '__main__':
    unittest.main()

from pprint import pprint
import unittest
from furl import furl
import profig
import requests
from nzb_search_result import NzbSearchResult

from search import Search
import search
from searchmodules.newznab import get_instance, NewzNab



class MyTestCase(unittest.TestCase):
    from config import cfg
    cfg = profig.Config('testsettings.cfg')
    
    cfg["search_providers.1.search_module"] = "newznab"
    cfg["search_providers.1.name"] = "NZBs.org"
    cfg["search_providers.1.apikey"] = "apikeynzbsorg"
    cfg["search_providers.1.base_url"] = "https://nzbs.org"
    cfg["search_providers.1.query_url"] = "http://127.0.0.1:5001/nzbsorg"
    
    cfg["search_providers.2.search_module"] = "newznab"
    cfg["search_providers.2.name"] = "DOGNzb"
    cfg["search_providers.2.apikey"] = "apikeydognzb"
    cfg["search_providers.2.base_url"] = "https://dognzb.cr"
    cfg["search_providers.2.query_url"] = "http://127.0.0.1:5001/dognzb"
    
    cfg.sync()
    
    def test_search_module_loading(self):
        assert len(search.search_modules) == 2
        
    def test_config(self):
        s = Search()
        providers = s.read_providers_from_config()
        assert len(providers) == 2
        for p in providers:
            print("Provider: " + p.name)
            
    def testSearchQueries(self):
        
        s = Search()
        s.providers = [NewzNab(self.cfg.section("search_providers").section("1"))]
        #TODO
        
    def testSearch(self):
        s = Search()
        results = s.search("avengers")
        self.assertEqual(200, len(results))
        
        
    def testSearchResultsToDict(self):
        from config import cfg
        n = NewzNab(cfg)
        #nzbsorg
        with open("tests/mock/nzbsorg_q_avengers_3results.json") as f:
            entries = n.process_query_result(f.read())
        from nzbmetasearch import render_search_results_for_api
        from nzbmetasearch import app
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

import re
import unittest
import sys
import logging
import profig
import requests
import responses
import search
import config
from pprint import pprint
from searchmodules.newznab import NewzNab
from flask import json
from furl import furl
from tests import mockbuilder

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")



class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.oldExecute_search_queries = search.execute_search_queries

    def tearDown(self):
        search.execute_search_queries = self.oldExecute_search_queries

    config.cfg = profig.Config()

    config.cfg["searching.timeout"] = 5

    config.cfg["search_providers.1.enabled"] = True
    config.cfg["search_providers.1.module"] = "newznab"
    config.cfg["search_providers.1.name"] = "NZBs.org"
    config.cfg["search_providers.1.query_url"] = "http://127.0.0.1:5001/nzbsorg"
    config.cfg["search_providers.1.apikey"] = "apikeynzbsorg"
    config.cfg["search_providers.1.search_types"] = ["general", "tv", "movie"]
    config.cfg["search_providers.1.search_ids"] = ["tvdbid", "rid", "imdbid"]
    config.cfg["search_providers.1.category_search"] = True

    config.cfg["search_providers.2.enabled"] = True
    config.cfg["search_providers.2.module"] = "newznab"
    config.cfg["search_providers.2.name"] = "DOGNzb"
    config.cfg["search_providers.2.query_url"] = "http://127.0.0.1:5001/dognzb"
    config.cfg["search_providers.2.apikey"] = "apikeydognzb"
    config.cfg["search_providers.2.search_types"] = ["general", "tv"]
    config.cfg["search_providers.2.search_ids"] = ["tvdbid", "rid"]
    config.cfg["search_providers.2.category_search"] = True
                                                  

    config.cfg["search_providers.3.enabled"] = True
    config.cfg["search_providers.3.module"] = "womble"
    config.cfg["search_providers.3.name"] = "womble"
    config.cfg["search_providers.3.query_url"] = "http://www.newshost.co.za/rss"
    config.cfg["search_providers.3.search_types"] = ["tv"]
    config.cfg["search_providers.3.supports_queries"] = False
    config.cfg["search_providers.3.search_ids"] = []
    config.cfg["search_providers.3.category_search"] = True
    
    config.cfg["search_providers.4.enabled"] = True
    config.cfg["search_providers.4.module"] = "nzbclub"
    config.cfg["search_providers.4.name"] = "nzbclub"
    config.cfg["search_providers.4.query_url"] = "https://member.nzbclub.com/nzbfeeds.aspx"
    config.cfg["search_providers.4.search_types"] = ["general", "tv", "movie"]
    config.cfg["search_providers.4.supports_queries"] = True
    config.cfg["search_providers.4.search_ids"] = []
    config.cfg["search_providers.4.generate_queries"] = True
    config.cfg["search_providers.4.category_search"] = False

    def test_search_module_loading(self):
        self.assertEqual(4, len(search.search_modules))

    def test_read_providers(self):
        providers = search.read_providers_from_config()
        self.assertEqual(4, len(providers))

    def test_pick_providers(self):
        search.read_providers_from_config()
        providers = search.pick_providers(search_type="general")
        self.assertEqual(3, len(providers))

        # Providers with tv search and which support queries (actually searching for particular releases)
        providers = search.pick_providers(search_type="tv", query_supplied=True)
        self.assertEqual(3, len(providers))

        # Providers with tv search, including those that only provide a list of latest releases (womble) but excluding the one that needs a query (nzbclub) 
        providers = search.pick_providers(search_type="tv", query_supplied=False)
        self.assertEqual(3, len(providers))

        providers = search.pick_providers(search_type="movie")
        self.assertEqual(2, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)
        self.assertEqual("NZBClub", providers[1].name)

        providers = search.pick_providers(identifier_key="tvdbid")
        self.assertEqual(2, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)
        self.assertEqual("DOGNzb", providers[1].name)

        providers = search.pick_providers("tv", identifier_key="imdbid")
        self.assertEqual(1, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)

    def testSearchResultsToDict(self):
        n = NewzNab(config.cfg)
        # nzbsorg
        with open("tests/mock/nzbsorg_q_avengers_3results.json") as f:
            entries = n.process_query_result(f.read())
        from nzbhydra import render_search_results_for_api
        from nzbhydra import app
        with app.test_request_context("/"):
            xhtml = render_search_results_for_api(entries)

    def testGeneralSearchProviderSelectionAndUrlBuilding(self):

        search.read_providers_from_config()

        from unittest.mock import MagicMock
        search.execute_search_queries = MagicMock(return_value=[])

        # General search, only providers which support queries
        search.search("aquery")
        args = search.execute_search_queries.call_args[0][0]  # mock returns a tuple, with the directional arguments as tuple first, of which we want the first (and only) argument, our actual arguments, which is a dict module:[urls]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]  # Url lists, sorted by name of provider because the order might be random
        self.assertEqual(3, len(args))  # both newznab providers and nzbclub

        url = args[0][0] #nzbclub
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "q=aquery" in web_args
        
        url = args[1][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=aquery" in web_args

        url = args[2][0]
        web_args = url.split("?")[1].split("&")  # and then we get all arguments because we cannot check against the url because furl builds it somewhat randomly
        assert "t=search" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "q=aquery" in web_args
        self.assertEqual(5, len(web_args))  # other args: o=json & extended=1


    @responses.activate
    def testTvSearchProviderSelectionAndUrlBuilding(self):

        search.read_providers_from_config()

        from unittest.mock import MagicMock
        search.execute_search_queries = MagicMock(return_value=[])

        # TV search without any specifics (return all lates releases), this includes wombles but excludes nzbclub 
        search.search_show()
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 3 providers (no nzbsorg

        url = args[0][0]
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args

        url = args[1][0]
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000 
        self.assertEqual(5, len(web_args))  # other args: o=json & extended=1      

        url = args[2][0]
        web_args = url.split("?")[1].split("&")
        assert "http://www.newshost.co.za/rss" in url
        self.assertEqual(1, len(web_args))  # only disable pretty titles



        # TV search with a query (not using identifiers), so no wombles
        search.search_show(query="aquery")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 3 providers

        url = args[0][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "q=aquery" in web_args
        assert "apikey=apikeydognzb" in web_args
        
        url = args[1][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        assert "q=aquery" in web_args
        

        
        url = args[2][0]
        assert "nzbs" in url
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "q=aquery" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000
        self.assertEqual(6, len(web_args))  # other args: o=json & extended=1


        url_re = re.compile(r'.*tvmaze.*')
        responses.add(responses.GET, url_re,
                      body=json.dumps({"name": "Breaking Bad"}), status=200,
                      content_type='application/json')


        # TV search with tvdbid, so no wombles
        search.search_show(identifier_key="tvdbid", identifier_value="81189")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 2 providers

        url = args[0][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "tvdbid=81189" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000
        self.assertEqual(6, len(web_args))  # other args: o=json & extended=1
        
        url = args[1][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        assert "q=Breaking+Bad" in web_args

        url = args[2][0]
        assert "nzbs" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "tvdbid=81189" in web_args
        assert "apikey=apikeynzbsorg" in web_args


        # TV search with tvdbid and season and episode
        search.search_show(identifier_key="tvdbid", identifier_value="81189", season=1, episode=2)
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 2 providers

        url = args[0][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "tvdbid=81189" in web_args
        assert "season=1" in web_args
        assert "ep=2" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000
        self.assertEqual(8, len(web_args))  # other args: o=json & extended=1
        
        url = args[1][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        assert "q=Breaking+Bad" in web_args

        url = args[2][0]
        assert "nzbs" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "tvdbid=81189" in web_args
        assert "season=1" in web_args
        assert "ep=2" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        
        
    @responses.activate
    def testMovieSearchProviderSelectionAndUrlBuilding(self):
        search.read_providers_from_config()

        from unittest.mock import MagicMock
        search.execute_search_queries = MagicMock(return_value=[])

        # movie search without any specifics (return all latest releases)
        search.search_movie()
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(1, len(args))  # only nzbsorg and supports general movie search without query (in this test

        url = args[0][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2000" in web_args  # no category provided, so we just added 2000
        self.assertEqual(5, len(web_args))  # other args: o=json & extended=1      



        # movie search with a query 
        search.search_movie(query="aquery")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(2, len(args))
        
        url = args[0][0] 
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=aquery" in web_args

        url = args[1][0]
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "q=aquery" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2000" in web_args  # no category provided, so we just added 2000
        self.assertEqual(6, len(web_args))  # other args: o=json & extended=1



        # movie search with imdbid, so a query should be generated for and used by nzbclub
        url_re = re.compile(r'.*omdbapi.*')
        responses.add(responses.GET, url_re,
                      body=json.dumps({"Title": "American Beauty"}), status=200,
                      content_type='application/json')
        search.search_movie(identifier_key="imdbid", identifier_value="tt0169547")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(2, len(args))  # 2 providers

        url = args[0][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=American+Beauty" in web_args
        

        url = args[1][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "imdbid=tt0169547" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2000" in web_args
        self.assertEqual(6, len(web_args))  # other args: o=json & extended=1


        # movie search with imdbid and category
        search.search_movie(identifier_key="imdbid", identifier_value="tt0169547", categories=[2040])
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(2, len(args))  # 2 providers
        
        url = args[0][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=American+Beauty" in web_args
        #todo category transformation for query based providers

        url = args[1][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "imdbid=tt0169547" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2040" in web_args
        self.assertEqual(6, len(web_args))  # other args: o=json & extended=1
        
        
        
        #Finally a test where we disable query generation
        # movie search with imdbid, so a query should be generated for and used by nzbclub
        config.cfg["searching.allow_query_generation"] = False
        url_re = re.compile(r'.*omdbapi.*')
        responses.add(responses.GET, url_re,
                      body=json.dumps({"Title": "American Beauty"}), status=200,
                      content_type='application/json')
        search.search_movie(identifier_key="imdbid", identifier_value="tt0169547")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(1, len(args))  # Only nzbs,org
        
        config.cfg["searching.allow_query_generation"] = True #set back for later tests

    @responses.activate
    def testSearchExecution(self):

        config.cfg["search_providers.1.enabled"] = True
        config.cfg["search_providers.1.module"] = "newznab"
        config.cfg["search_providers.1.name"] = "NZBs.org"
        config.cfg["search_providers.1.query_url"] = "http://127.0.0.1:5001/nzbsorg"
        config.cfg["search_providers.1.search_types"] = "general, tv, movie"
        config.cfg["search_providers.1.search_ids"] = "tvdbid, rid, imdbid"

        config.cfg["search_providers.2.enabled"] = True
        config.cfg["search_providers.2.module"] = "newznab"
        config.cfg["search_providers.2.name"] = "DOGNzb"
        config.cfg["search_providers.2.query_url"] = "http://127.0.0.1:5001/dognzb"
        config.cfg["search_providers.2.search_types"] = "general, tv"
        config.cfg["search_providers.2.search_ids"] = "tvdbid, rid"

        config.cfg["search_providers.3.enabled"] = True
        config.cfg["search_providers.3.module"] = "womble"
        config.cfg["search_providers.3.name"] = "womble"
        config.cfg["search_providers.3.query_url"] = "http://www.newshost.co.za/rss"
        config.cfg["search_providers.3.search_types"] = "tv"
        config.cfg["search_providers.3.supports_queries"] = False
        config.cfg["search_providers.3.search_ids"] = []


        # movie search without any specifics (return all latest releases)
        search.read_providers_from_config()

        mockitem_nzbs = mockbuilder.buildNewznabItem("myId", "myTitle", "myGuid", "http://nzbs.org/myId.nzb", None, None, 12345, "NZBs.org", [2000, 2040])
        mockresponse_nzbs = mockbuilder.buildNewznabResponse("NZBs.org", [mockitem_nzbs])

        url_re = re.compile(r'.*nzbsorg.*')
        responses.add(responses.GET, url_re,
                      body=json.dumps(mockresponse_nzbs), status=200,
                      content_type='application/json')
        
        
        results = search.search_movie()
        self.assertEqual(1, len(results))
        result = results[0]
        self.assertEqual("myTitle", result.title)
        assert 2000 in result.categories
        assert 2040 in result.categories
        
        
    @responses.activate
    def testSearchExceptions(self):
        config.cfg["search_providers.1.enabled"] = True
        config.cfg["search_providers.1.module"] = "newznab"
        config.cfg["search_providers.1.name"] = "NZBs.org"
        config.cfg["search_providers.1.query_url"] = "http://127.0.0.1:5001/nzbsorg"
        config.cfg["search_providers.1.search_types"] = "general, tv, movie"
        config.cfg["search_providers.1.search_ids"] = "tvdbid, rid, imdbid"

        config.cfg["search_providers.2.enabled"] = False

        config.cfg["search_providers.3.enabled"] = False

        # movie search without any specifics (return all latest releases)
        search.read_providers_from_config()
        
        from tests.testLogger import LoggingCaptor
        from log import setup_custom_logger
        logger = setup_custom_logger("root")
        logging_captor = LoggingCaptor()
        logger.addHandler(logging_captor)
        
        with responses.RequestsMock() as rsps:
            url_re = re.compile(r'.*')
            rsps.add(responses.GET, url_re,
                          body='<error code="100" description="Incorrect user credentials"/>', status=200,
                          content_type='application/json')        
            search.search_movie()
            assert any("The API key seems to be incorrect" in s for s in logging_captor.messages)
        
        with responses.RequestsMock() as rsps:
            logging_captor.messages = []
            url_re = re.compile(r'.*')
            rsps.add(responses.GET, url_re,
                          body='', status=404,
                          content_type='application/json')        
            search.search_movie()
            assert any("Unable to connect with" in s for s in logging_captor.messages)
            
        



        

    # For creating test data
    def getMockResponse(self, action, category=None, rid=None, imdbid=None, season=None, episode=None, q=None):
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
        # Enable to create mock responses
        if False:
            self.getMock("search")  # all
            self.getMock("search", q="avengers")  # general search avengers
            self.getMock("search", q="avengers", category="2000")  # general search avengers all movies
            self.getMock("search", category="5030")  # all tv sd
            self.getMock("search", category="5040")  # all tv hd

            self.getMock("tvsearch")  # tvsearch all
            self.getMock("tvsearch", category="5030")  # tvsearch all sd
            self.getMock("tvsearch", category="5040")  # tvsearch all hd
            self.getMock("tvsearch", category="5040", rid=80379)  # bbt hd
            self.getMock("tvsearch", category="5030", rid=80379)  # bbt sd
            self.getMock("tvsearch", category="5040", rid=80379, season=1)  # bbt hd season 1
            self.getMock("tvsearch", category="5040", rid=80379, season=1, episode=2)  # bbt hd season 1 episode 2

            self.getMock("movie")  # moviesearch all
            self.getMock("movie", category="2040")  # moviesearch all hd
            self.getMock("movie", category="2030")  # moviesearch all sd
            self.getMock("movie", imdbid="0169547")  # moviesearch american beauty all
            self.getMock("movie", category="2040", imdbid="0169547")  # moviesearch american beauty all hd


if __name__ == '__main__':
    unittest.main()

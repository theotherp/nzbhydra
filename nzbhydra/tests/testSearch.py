import re
import unittest
import sys
import logging
from pprint import pprint
import json

import arrow
from freezegun import freeze_time
import profig
import requests
import responses
from furl import furl

from nzbhydra import search, config, search_module, database
from nzbhydra.tests import mockbuilder

from nzbhydra.database import Provider
from nzbhydra.tests.db_prepare import set_and_drop

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")

set_and_drop()
Provider(module="newznab", name="NZBs.org", settings={"apikey": "apikeynzbsorg", "query_url": "http://127.0.0.1:5001/nzbsorg", "base_url": "http://127.0.0.1:5001/nzbsorg", "search_types": ["tv", "general", "movie"], "search_ids": ["imdbid", "tvdbid", "rid"]}).save()
Provider(module="newznab", name="DOGNzb", settings={"apikey": "apikeydognzb", "query_url": "http://127.0.0.1:5001/dognzb", "base_url": "http://127.0.0.1:5001/dognzb", "search_types": ["tv", "general"], "search_ids": ["tvdbid", "rid"]}).save()
Provider(module="nzbclub", name="NZBClub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_types": ["general", "tv", "movie"], "search_ids": [], "generate_queries": True}).save()
Provider(module="womble", name="womble", settings={"query_url": "http://www.newshost.co.za/rss", "base_url": "http://127.0.0.1:5001/womble", "search_types": ["tv"]}).save()


class MyTestCase(unittest.TestCase):
    def setUp(self):
        self.oldExecute_search_queries = search.execute_search_queries
        database.ProviderStatus.delete().execute()
        database.ProviderSearch.delete().execute()
        database.ProviderSearchApiAccess.delete().execute()

    def tearDown(self):
        search.execute_search_queries = self.oldExecute_search_queries

    config.cfg = profig.Config()

    config.cfg["searching.timeout"] = 5

    def test_search_module_loading(self):
        self.assertEqual(5, len(search.search_modules))

    def test_read_providers(self):
        providers = search.read_providers_from_config()
        self.assertEqual(4, len(providers))

    def test_pick_providers(self):
        search.read_providers_from_config()
        Provider().select().count()
        providers = search.pick_providers()
        self.assertEqual(3, len(providers))

        # Providers with tv search and which support queries (actually searching for particular releases)
        providers = search.pick_providers(query_supplied=True)
        self.assertEqual(3, len(providers))

        # Providers with tv search, including those that only provide a list of latest releases (womble) but excluding the one that needs a query (nzbclub) 
        providers = search.pick_providers(query_supplied=False)
        self.assertEqual(3, len(providers))

        providers = search.pick_providers(identifier_key="tvdbid")
        self.assertEqual(2, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)
        self.assertEqual("DOGNzb", providers[1].name)

        providers = search.pick_providers("tv", identifier_key="imdbid")
        self.assertEqual(1, len(providers))
        self.assertEqual("NZBs.org", providers[0].name)

    def testGeneralSearchProviderSelectionAndUrlBuilding(self):

        search.read_providers_from_config()

        from unittest.mock import MagicMock
        search.execute_search_queries = MagicMock(return_value=[])

        # General search, only providers which support queries
        search.search("aquery")
        args = search.execute_search_queries.call_args[0][0]  # mock returns a tuple, with the directional arguments as tuple first, of which we want the first (and only) argument, our actual arguments, which is a dict module:[urls]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]  # Url lists, sorted by name of provider because the order might be random
        self.assertEqual(3, len(args))  # both newznab providers and nzbclub

        url = args[0]["queries"][0]  # nzbclub
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "q=aquery" in web_args

        url = args[1]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=aquery" in web_args

        url = args[2]["queries"][0]
        web_args = url.split("?")[1].split("&")  # and then we get all arguments because we cannot check against the url because furl builds it somewhat randomly
        assert "t=search" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "q=aquery" in web_args

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

        url = args[0]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args

        url = args[1]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000 
        self.assertEqual(7, len(web_args))  # other args: o=json & extended=1 & offset & limit      

        url = args[2]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "http://www.newshost.co.za/rss" in url
        self.assertEqual(1, len(web_args))  # only disable pretty titles



        # TV search with a query (not using identifiers), so no wombles
        search.search_show(query="aquery")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 3 providers

        url = args[0]["queries"][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "q=aquery" in web_args
        assert "apikey=apikeydognzb" in web_args

        url = args[1]["queries"][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        assert "q=aquery" in web_args

        url = args[2]["queries"][0]
        assert "nzbs" in url
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "q=aquery" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000

        url_re = re.compile(r'.*tvmaze.*')
        responses.add(responses.GET, url_re, body=json.dumps({"name": "Breaking Bad"}), status=200, content_type='application/json')


        # TV search with tvdbid, allow query generation, so no wombles or nzbclub
        search.search_show(identifier_key="tvdbid", identifier_value="81189")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 

        url = args[0]["queries"][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "tvdbid=81189" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000

        url = args[1]["queries"][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        # todo query generation

        url = args[2]["queries"][0]
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

        url = args[0]["queries"][0]
        assert "dognzb" in url
        web_args = url.split("?")[1].split("&")
        assert "t=tvsearch" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "tvdbid=81189" in web_args
        assert "season=1" in web_args
        assert "ep=2" in web_args
        assert "cat=5000" in web_args  # no category provided, so we just added 5000

        url = args[1]["queries"][0]
        assert "nzbclub" in url
        web_args = url.split("?")[1].split("&")
        assert "q=Breaking+Bad+s01e02+or+Breaking+Bad+1x02" in web_args

        url = args[2]["queries"][0]
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
        self.assertEqual(3, len(args))

        url = args[0]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "apikey=apikeydognzb" in web_args
        assert "cat=2000" in web_args  # no category provided, so we just added 2000
        


        # movie search with a query 
        search.search_movie(query="aquery")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))

        url = args[0]["queries"][0]
        assert "dognzb" in url

        url = args[1]["queries"][0]
        assert "nzbclub" in url
        

        url = args[2]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=search" in web_args
        assert "q=aquery" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2000" in web_args  # no category provided, so we just added 2000



        # movie search with imdbid, so a query should be generated for and used by nzbclub
        url_re = re.compile(r'.*omdbapi.*')
        responses.add(responses.GET, url_re,
                      body=json.dumps({"Title": "American Beauty"}), status=200,
                      content_type='application/json')
        search.search_movie(imdbid="tt0169547")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 2 providers

        url = args[0]["queries"][0]
        assert "dognzb" in url
        
        url = args[1]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=American+Beauty" in web_args

        url = args[2]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "imdbid=tt0169547" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2000" in web_args


        # movie search with imdbid and category
        search.search_movie(imdbid="tt0169547", category="Movies SD")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(3, len(args))  # 2 providers

        url = args[1]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "nzbclub" in url
        assert "q=American+Beauty" in web_args
        # todo category transformation for query based providers

        url = args[2]["queries"][0]
        web_args = url.split("?")[1].split("&")
        assert "t=movie" in web_args
        assert "imdbid=tt0169547" in web_args
        assert "apikey=apikeynzbsorg" in web_args
        assert "cat=2030" in web_args

        # Finally a test where we disable query generation
        # movie search with imdbid, so a query should be generated for and used by nzbclub
        config.cfg["searching.allow_query_generation"] = False
        url_re = re.compile(r'.*omdbapi.*')
        responses.add(responses.GET, url_re,
                      body={"Title": "American Beauty"}, status=200,
                      content_type='application/json')
        search.search_movie(imdbid="tt0169547")
        args = search.execute_search_queries.call_args[0][0]
        args = [args[y] for y in sorted(args, key=lambda x: x.name)]
        self.assertEqual(1, len(args))  # Only nzbs,org

        config.cfg["searching.allow_query_generation"] = True  # set back for later tests

    @responses.activate
    def testSearchExecution(self):

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
        # movie search without any specifics (return all latest releases)
        search.read_providers_from_config()

        from nzbhydra.tests.testLogger import LoggingCaptor
        from nzbhydra.log import setup_custom_logger
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

    def testHandleProviderFailureAndSuccess(self):
        provider_model = Provider.get(Provider.name == "NZBs.org")
        with freeze_time("2015-09-20 14:00:00", tz_offset=-4):
            sm = search_module.SearchModule(provider_model)
            sm.handle_provider_failure(provider_model)
            # First error, so level 1
            self.assertEqual(1, provider_model.status.get().level)
            now = arrow.utcnow()
            first_failure = arrow.get(arrow.get(provider_model.status.get().first_failure))
            disabled_until = arrow.get(provider_model.status.get().disabled_until)
            self.assertEqual(now, first_failure)
            self.assertEqual(now.replace(minutes=+sm.disable_periods[1]), disabled_until)

            sm.handle_provider_failure()
            self.assertEqual(2, provider_model.status.get().level)
            disabled_until = arrow.get(provider_model.status.get().disabled_until)
            self.assertEqual(now.replace(minutes=+sm.disable_periods[2]), disabled_until)

            sm.handle_provider_success()
            self.assertEqual(1, provider_model.status.get().level)
            self.assertEqual(arrow.get(0), provider_model.status.get().disabled_until)
            self.assertIsNone(provider_model.status.get().reason)

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

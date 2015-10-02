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
from nzbhydra.tests.providerTest import ProviderTestcase

logging.getLogger("root").addHandler(logging.StreamHandler(sys.stdout))
logging.getLogger("root").setLevel("DEBUG")

set_and_drop()
Provider(module="newznab", name="NZBs.org", settings={"apikey": "apikeynzbsorg", "query_url": "http://127.0.0.1:5001/nzbsorg", "base_url": "http://127.0.0.1:5001/nzbsorg", "search_types": ["tv", "general", "movie"], "search_ids": ["imdbid", "tvdbid", "rid"]}).save()
Provider(module="newznab", name="DOGNzb", settings={"apikey": "apikeydognzb", "query_url": "http://127.0.0.1:5001/dognzb", "base_url": "http://127.0.0.1:5001/dognzb", "search_types": ["tv", "general"], "search_ids": ["tvdbid", "rid"]}).save()
Provider(module="nzbclub", name="NZBClub", settings={"query_url": "http://127.0.0.1:5001/nzbclub", "base_url": "http://127.0.0.1:5001/nzbclub", "search_types": ["general", "tv", "movie"], "search_ids": [], "generate_queries": True}).save()
Provider(module="womble", name="womble", settings={"query_url": "http://www.newshost.co.za/rss", "base_url": "http://127.0.0.1:5001/womble", "search_types": ["tv"]}).save()


class MyTestCase(ProviderTestcase):
    def setUp(self):
        self.oldExecute_search_queries = search.start_search_futures
        database.ProviderStatus.delete().execute()
        database.ProviderSearch.delete().execute()

    def tearDown(self):
        search.start_search_futures = self.oldExecute_search_queries

    config.cfg = profig.Config()

    config.cfg["searching.timeout"] = 5

    def test_search_module_loading(self):
        self.assertEqual(5, len(search.search_modules))

    def test_read_providers(self):
        providers = search.read_providers_from_config()
        self.assertEqual(4, len(providers))

    def test_pick_providers(self):
        search.read_providers_from_config()

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

        # Test category search, the first provider is now only enabled for audio searches, so it will be only 2 available 
        search.providers[0].provider.settings["categories"] = ["Audio"]
        providers = search.pick_providers(category="Movie")
        self.assertEqual(2, len(providers))


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

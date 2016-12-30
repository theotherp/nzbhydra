from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import pytest
from bunch import Bunch

# standard_library.install_aliases()
from builtins import *
import re
from freezegun import freeze_time
import responses

from nzbhydra import config
from nzbhydra.categories import getCategoryByAnyInput
from nzbhydra.database import Indexer
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.newznab import NewzNab
from nzbhydra.tests.UrlTestCase import UrlTestCase
from nzbhydra.tests.db_prepare import set_and_drop


class NewznabTests(UrlTestCase):
    def setUp(self):
        set_and_drop()

        self.indexercom = Indexer(name="indexer.com")
        #self.indexercom.save()

        self.newznab1 = Bunch()
        self.newznab1.enabled = True
        self.newznab1.name = "indexer.com"
        self.newznab1.host = "https://indexer.com"
        self.newznab1.apikey = "apikeyindexer.com"
        self.newznab1.timeout = None
        self.newznab1.score = 0
        self.newznab1.backend = "newznab"
        self.newznab1.search_ids = ["imdbid", "rid", "tvdbid"]
        self.newznab1.searchTypes = []
        self.n1 = NewzNab(self.newznab1)

    @freeze_time("2015-10-12 18:00:00", tz_offset=-4)
    def testParseSearchResult(self):
        # nzbsorg
        with open("mock/indexercom_q_testtitle_3results.xml") as f:
            self.n1.parseXml(f.read())
            entries = self.n1.process_query_result(f.read(), SearchRequest()).entries
        self.assertEqual(3, len(entries))

        self.assertEqual(entries[0].title, "testtitle1")
        assert entries[0].size == 2893890900
        assert entries[0].indexerguid == "eff551fbdb69d6777d5030c209ee5d4b"
        self.assertEqual(entries[0].age_days, 1)
        self.assertEqual(entries[0].epoch, 1444584857)
        self.assertEqual(entries[0].pubdate_utc, "2015-10-11T17:34:17+00:00")
        self.assertEqual(entries[0].poster, "chuck@norris.com")
        self.assertEqual(entries[0].group, "alt.binaries.mom")
        self.assertEqual(entries[0].details_link, "https://indexer.com/details/eff551fbdb69d6777d5030c209ee5d4b")

        # Pull group from description
        self.assertEqual(entries[1].group, "alt.binaries.hdtv.x264")
        # Use "usenetdate" attribute if available
        self.assertEqual(entries[1].pubdate_utc, "2015-10-03T22:22:22+00:00")  # Sat, 03 Oct 2015 22:22:22 +0000
        # Use "info" attribute if available
        self.assertEqual(entries[0].details_link, "https://indexer.com/details/eff551fbdb69d6777d5030c209ee5d4b")

        # Don't use "not available" as group
        self.assertIsNone(entries[2].group)

        self.assertEqual("English testtitle2", entries[1].title)
        self.assertEqual("testtitle3", entries[2].title)

    # @freeze_time("2016-01-30 18:00:00", tz_offset=-4)
    # def testParseSpotwebSearchResult(self):
    #     # nzbsorg
    #     with open("mock/spotweb_q_testtitle_3results.xml") as f:
    #         entries = self.n1.process_query_result(f.read(), SearchRequest()).entries
    #     self.assertEqual(3, len(entries))
    #
    #     self.assertEqual(entries[0].title, "testtitle1")
    #     assert entries[0].size == 3960401206
    #     assert entries[0].indexerguid == "ESOSxziB5WAYyalVgTP8M@spot.net"
    #     self.assertEqual(entries[0].age_days, 5)
    #     self.assertEqual(entries[0].epoch, 1453663845)
    #     self.assertEqual(entries[0].pubdate_utc, "2016-01-24T19:30:45+00:00")
    #     self.assertEqual(entries[0].poster, "SluweSjakie@spot.net")
    #     self.assertIsNone(entries[0].group)
    #
    # @freeze_time("2016-01-11 18:00:00", tz_offset=0)
    # def testPirateNzbParseSearchResult(self):
    #     # nzbsorg
    #     with open("mock/piratenzb_movies_response.xml") as f:
    #         entries = self.n1.process_query_result(f.read(), SearchRequest()).entries
    #     self.assertEqual(3, len(entries))
    #
    #     self.assertEqual(entries[0].title, "title1")
    #     assert entries[0].size == 954926472
    #     assert entries[0].indexerguid == "d4776501c2b409c41f0649afc1e2d6d3f033119e"
    #     self.assertEqual(entries[0].age_days, 323)
    #     self.assertEqual(entries[0].epoch, 1424552357)
    #     self.assertEqual(entries[0].pubdate_utc, "2015-02-21T20:59:17+00:00")
    #     self.assertEqual(entries[0].details_link, "https://indexer.com/details/d4776501c2b409c41f0649afc1e2d6d3f033119e")
    #
    # def testNewznabSearchQueries(self):
    #     self.args = SearchRequest(query="aquery")
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&q=aquery&t=search", query)
    #
    #     self.args = SearchRequest(query=None)
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&t=search", query)
    #
    #     self.args = SearchRequest(query="")
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&t=search", query)
    #
    #     self.args = SearchRequest(category=getCategoryByAnyInput("audio"))
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=3000&extended=1&limit=100&offset=0&t=search", query)
    #
    #     self.args = SearchRequest()
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&extended=1&limit=100&offset=0&t=tvsearch", query)
    #
    #     self.args = SearchRequest(query=None)
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&extended=1&limit=100&offset=0&t=tvsearch", query)
    #
    #     self.args = SearchRequest(query="")
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&extended=1&limit=100&offset=0&t=tvsearch", query)
    #
    #     self.args = SearchRequest(category=getCategoryByAnyInput("all"))
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&t=tvsearch", query)
    #
    #     self.args = SearchRequest(identifier_value="8511", identifier_key="rid")
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&extended=1&limit=100&offset=0&rid=8511&t=tvsearch", query)
    #
    #     self.args = SearchRequest(identifier_value="8511", identifier_key="rid", season=1)
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&extended=1&limit=100&offset=0&rid=8511&season=1&t=tvsearch", query)
    #
    #     self.args = SearchRequest(identifier_value="8511", identifier_key="rid", season=1, episode=2)
    #     queries = self.n1.get_showsearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=5000&ep=2&extended=1&limit=100&offset=0&rid=8511&season=1&t=tvsearch", query)
    #
    #     self.args = SearchRequest(identifier_value="12345678", identifier_key="imdbid")
    #     queries = self.n1.get_moviesearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=2000&extended=1&imdbid=12345678&limit=100&offset=0&t=movie", query)
    #
    #     self.args = SearchRequest(identifier_value="12345678", identifier_key="imdbid", category=getCategoryByAnyInput("movieshd"))
    #     queries = self.n1.get_moviesearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=2040,2050,2060&extended=1&imdbid=12345678&limit=100&offset=0&t=movie", query)
    #
    #     self.args = SearchRequest(category=getCategoryByAnyInput("movies"))
    #     queries = self.n1.get_moviesearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=2000&extended=1&limit=100&offset=0&t=movie", query)
    #
    #     self.args = SearchRequest(category=getCategoryByAnyInput("movies"), query=None)
    #     queries = self.n1.get_moviesearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=2000&extended=1&limit=100&offset=0&t=movie", query)
    #
    #     self.args = SearchRequest(category=getCategoryByAnyInput("movies"), query="")
    #     queries = self.n1.get_moviesearch_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=2000&extended=1&limit=100&offset=0&t=movie", query)
    #
    #     config.settings.searching.forbiddenWords = "ignorethis"
    #     self.args = SearchRequest(query="aquery", forbiddenWords=["ignorethis"])
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&q=aquery !ignorethis&t=search", query)
    #
    #     config.settings.searching.forbiddenWords = "ignorethis"
    #     self.args = SearchRequest(query="aquery", forbiddenWords=["ignorethis"])
    #     queries = self.n1.get_search_urls(self.args)
    #     assert len(queries) == 1
    #     query = queries[0]
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&extended=1&limit=100&offset=0&q=aquery !ignorethis&t=search", query)
    #
    #
    #
    # @responses.activate
    # def testGetNfo(self):
    #     with open("mock/nfo.xml", encoding="latin-1") as f:
    #         xml = f.read()
    #     with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
    #         url_re = re.compile(r'.*')
    #         rsps.add(responses.GET, url_re,
    #                  body=xml, status=200,
    #                  content_type='application/x-html')
    #         hasnfo, nfo, message = self.n1.get_nfo("b4ba74ecb5f5962e98ad3c40c271dcc8")
    #         self.assertTrue(hasnfo)
    #         self.assertEqual("an nfo in xml", nfo)
    #
    #     with open("mock/rawnfo.txt", encoding="latin-1") as f:
    #         xml = f.read()
    #     with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
    #         url_re = re.compile(r'.*')
    #         rsps.add(responses.GET, url_re,
    #                  body=xml, status=200,
    #                  content_type='application/x-html')
    #         hasnfo, nfo, message = self.n1.get_nfo("b4ba74ecb5f5962e98ad3c40c271dcc8")
    #         self.assertTrue(hasnfo)
    #         self.assertEqual("a raw nfo", nfo)
    #
    #     with open("mock/nfo-noresult.xml", encoding="latin-1") as f:
    #         xml = f.read()
    #     with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
    #         url_re = re.compile(r'.*')
    #         rsps.add(responses.GET, url_re,
    #                  body=xml, status=200,
    #                  content_type='application/x-html')
    #         hasnfo, nfo, message = self.n1.get_nfo("b4ba74ecb5f5962e98ad3c40c271dcc8")
    #         self.assertFalse(hasnfo)
    #         self.assertEqual("No NFO available", message)
    #
    #     with open("mock/nfo-nosuchitem.xml", encoding="latin-1") as f:
    #         xml = f.read()
    #     with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
    #         url_re = re.compile(r'.*')
    #         rsps.add(responses.GET, url_re,
    #                  body=xml, status=200,
    #                  content_type='application/x-html')
    #         hasnfo, nfo, message = self.n1.get_nfo("b4ba74ecb5f5962e98ad3c40c271dcc8")
    #         self.assertFalse(hasnfo)
    #         self.assertEqual("No NFO available", message)
    #
    # def testGetNzbLink(self):
    #     link = self.n1.get_nzb_link("guid", None)
    #     assert "id=guid" in link
    #     assert "t=get" in link
    #
    #
    # def testGetEbookUrls(self):
    #
    #     searchRequest = SearchRequest(query="novel")
    #     urls = self.n1.get_ebook_urls(searchRequest)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=7020,8010&limit=100&t=search&extended=1&offset=0&q=novel", urls[0])
    #
    #     self.args = SearchRequest(author="anauthor", title="atitle", category=getCategoryByAnyInput(7020))
    #     queries = self.n1.get_ebook_urls(self.args)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&cat=7020&extended=1&limit=100&offset=0&q=anauthor+atitle&t=search", queries[0])
    #
    #     self.newznab1.searchTypes = ["book"]
    #     self.n1 = NewzNab(self.newznab1)
    #     self.args = SearchRequest(author="anauthor", title="atitle", category=getCategoryByAnyInput(7020))
    #     queries = self.n1.get_ebook_urls(self.args)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&author=anauthor&cat=7020&extended=1&limit=100&offset=0&t=book&title=atitle", queries[0])
    #
    # def testGetMovieSearchUrls(self):
    #     self.newznab1.search_ids = ["imdbid"]
    #     # Doing a query based movie search uses regular search with the proper category
    #     searchRequest = SearchRequest(type="movie", query="atitle")
    #     urls = self.n1.get_moviesearch_urls(searchRequest)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=search&extended=1&offset=0&cat=2000&q=atitle", urls[0])
    #
    #     searchRequest = SearchRequest(type="movie", identifier_key="imdbid", identifier_value="123")
    #     urls = self.n1.get_moviesearch_urls(searchRequest)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=movie&extended=1&offset=0&cat=2000&imdbid=123", urls[0])
    #
    # def testGetShowSearchUrls(self):
    #     self.newznab1.search_ids = ["tvdbid", "rid"]
    #     self.args = SearchRequest(identifier_value="47566", identifier_key="rid")
    #     urls = self.n1.get_showsearch_urls(self.args)
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=tvsearch&extended=1&offset=0&cat=5000&rid=47566", urls[0])
    #     self.args = SearchRequest(identifier_value="299350", identifier_key="tvdbid")
    #     urls = self.n1.get_showsearch_urls(self.args)
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=tvsearch&extended=1&offset=0&cat=5000&tvdbid=299350", urls[0])
    #
    # def testThatShowSearchIdsAreConverted(self):
    #     self.newznab1.search_ids = ["tvdbid"]
    #     self.args = SearchRequest(identifier_value="47566", identifier_key="rid")
    #     urls = self.n1.get_showsearch_urls(self.args)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=tvsearch&extended=1&offset=0&cat=5000&tvdbid=299350", urls[0])
    #
    #     self.newznab1.search_ids = ["rid"]
    #     self.args = SearchRequest(identifier_value="299350", identifier_key="tvdbid")
    #     urls = self.n1.get_showsearch_urls(self.args)
    #     self.assertEqual(1, len(urls))
    #     self.assertUrlEqual("https://indexer.com/api?apikey=apikeyindexer.com&limit=100&t=tvsearch&extended=1&offset=0&cat=5000&rid=47566", urls[0])
    #
    # def testThatNoUrlsAreReturnedIfIdCannotBeConverted(self):
    #     self.newznab1.search_ids = ["unknownid"]
    #     self.args = SearchRequest(identifier_value="299350", identifier_key="tvdbid")
    #     urls = self.n1.get_showsearch_urls(self.args)
    #     self.assertEqual(0, len(urls))
    #
    # def testCheckAuth(self):
    #     body = '<?xml version="1.0" encoding="utf-8" ?><error code="100" description="Incorrect user credentials" />'
    #     with pytest.raises(Exception) as excinfo:
    #         self.n1.check_auth(body)
    #     self.assertEqual("The API key seems to be incorrect.", excinfo.value.message)
    #
    #     body = '<?xml version="1.0" encoding="utf-8" ?><error code="910" description="API Temporarily Disabled (daily maintenance)" />'
    #     with pytest.raises(Exception) as excinfo:
    #         self.n1.check_auth(body)
    #     self.assertEqual("The API seems to be disabled for the moment.", excinfo.value.message)
    #
    #     body = '<?xml version="1.0" encoding="utf-8" ?><error code="200" description="Missing parameter" />'
    #     with pytest.raises(Exception) as excinfo:
    #         self.n1.check_auth(body)
    #     self.assertEqual("Unknown error while trying to access the indexer: Missing parameter", excinfo.value.message)
    #
    # @responses.activate
    # def testGetEntryById(self):
    #     with open("mock/indexercom_details.xml", encoding="latin-1") as f:
    #         xml = f.read()
    #     with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
    #         url_re = re.compile(r'.*')
    #         rsps.add(responses.GET, url_re,
    #                  body=xml, status=200,
    #                  content_type='application/x-html')
    #         item = self.n1.get_entry_by_id("aguid", "atitle")
    #         self.assertEqual("testtitle1", item.title)
    #         self.assertEqual(2893890900, item.size)

from __future__ import print_function
from __future__ import unicode_literals
from __future__ import division
from __future__ import absolute_import

import unittest

import responses
from builtins import open
from future import standard_library
#standard_library.install_aliases()
from builtins import *
from freezegun import freeze_time
from furl import furl
import pytest
import requests
import re

from nzbhydra import config
from nzbhydra.database import Indexer
from nzbhydra.indexers import getIndexerSettingByName
from nzbhydra.search import SearchRequest
from nzbhydra.searchmodules.nzbindex import NzbIndex
from nzbhydra.tests.UrlTestCase import UrlTestCase
from nzbhydra.tests.db_prepare import set_and_drop


class NzbIndexTests(UrlTestCase):
    @pytest.fixture
    def setUp(self):
        set_and_drop()

    def testUrlGeneration(self):
        w = NzbIndex(getIndexerSettingByName("nzbindex"))
        self.args = SearchRequest(query="a showtitle", season=1, episode=2)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        print(urls[0])
        self.assertEqual('a showtitle s01e02 | 1x02', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="a showtitle", season=1, episode=None)
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle s01 | "season 1"', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="a showtitle", season="2016", episode="08/08")
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual('a showtitle "2016 08 08"', furl(urls[0]).args["q"])

        self.args = SearchRequest(query="aquery", forbiddenWords=["ignorethis"])
        urls = w.get_showsearch_urls(self.args)
        self.assertEqual(1, len(urls))
        self.assertEqual("https://nzbindex.com/search?max=100&hidecross=1&more=1&q=aquery+-ignorethis", urls[0])


        
    @ freeze_time("2015-10-03 20:15:00", tz_offset=+2)
    def testProcess_results(self):
        w = NzbIndex(getIndexerSettingByName("nzbindex"))
        with open("mock/nzbindex--q-testtitle.html") as f:
            processing_result = w.process_query_result(f.read(), SearchRequest())
            entries = processing_result.entries
            self.assertEqual('114143855', entries[0].indexerguid)
            self.assertEqual('testtitle1', entries[0].title)
            self.assertFalse(entries[0].has_nfo)
            self.assertEqual('bowibow@gmail.com (senior)', entries[0].poster)
            self.assertEqual('alt.binaries.mom', entries[0].group)
            self.assertEqual("https://nzbindex.com/download/114143855/testtitle1-testtitle1.nzb", entries[0].link)
            self.assertEqual(169103851, entries[0].size)
            self.assertEqual("2014-11-04T10:39:00+01:00", entries[0].pubdate_utc)  # would be perfect, that is the exact pubdate 
            self.assertEqual("Tue, 04 Nov 2014 10:39:00 +0100", entries[0].pubDate)   
            self.assertEqual(1415093940, entries[0].epoch)
            self.assertEqual(333, entries[0].age_days)
            self.assertEqual("https://nzbindex.com/release/114143855/testtitle1-testtitle1.nzb", entries[0].details_link)
            self.assertTrue(entries[0].passworded)

            self.assertEqual(0, entries[1].age_days)
            self.assertEqual("2015-10-03T20:15:00+01:00", entries[1].pubdate_utc)  # would be perfect, that is the exact pubdate 
            self.assertEqual(1443899700, entries[1].epoch)

            self.assertEqual(1000, processing_result.total)
            self.assertTrue(processing_result.has_more)
   

    def testGetNzbLink(self):
        n = NzbIndex(getIndexerSettingByName("nzbindex"))
        link = n.get_nzb_link("guid", "title")
        self.assertEqual("https://nzbindex.com/download/guid/title.nzb", link)

    @responses.activate
    def testGetEntryById(self):
        Indexer(name="nzbindex").save()
        n = NzbIndex(getIndexerSettingByName("nzbindex"))
        with open("mock/nzbindex--details.html", encoding="latin-1") as f:
            xml = f.read()
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            url_re = re.compile(r'.*')
            rsps.add(responses.GET, url_re,
                     body=xml, status=200,
                     content_type='application/x-html')
            item = n.get_entry_by_id("aguid", "atitle")
            self.assertEqual("atitle", item.title)
            self.assertEqual(3816816, item.size)
            self.assertEqual("alt.binaries.pwp | alt.binaries.usenetrevolution", item.group)
            self.assertEqual("janusch@gmail.com (Janusch)", item.poster)
            self.assertEqual("https://nzbindex.com/download/aguid/atitle.nzb", item.link)
            self.assertEqual("https://nzbindex.com/release/aguid/atitle.nzb", item.details_link)
            
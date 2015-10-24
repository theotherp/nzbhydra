import json
from pprint import pprint
import re
import unittest
from freezegun import freeze_time
import responses
from nzbhydra import config
from nzbhydra.database import Provider
from nzbhydra.search import SearchRequest

from nzbhydra.searchmodules.newznab import NewzNab
from nzbhydra.tests import mockbuilder
from nzbhydra.tests.db_prepare import set_and_drop
from nzbhydra.tests.providerTest import ProviderTestcase


class MyTestCase(ProviderTestcase):

    def setUp(self):    
        set_and_drop()
        config.load("testsettings.cfg")
        self.nzbsorgdb = Provider(name="NZBs.org")
        self.nzbsorgdb.save()
        self.dognzbdb = Provider(name="DOGNzb")
        self.dognzbdb.save()
        
        
        config.providerSettings.newznab1.enabled = True
        config.providerSettings.newznab1.host.set("http://127.0.0.1:5001/nzbsorg")
        config.providerSettings.newznab1.apikey.set("apikeynzbsorg")
        self.n1 = NewzNab(config.providerSettings.newznab1)
        self.n2 = NewzNab(config.providerSettings.newznab2)
        
    
    @freeze_time("2015-10-12 20:00:00", tz_offset=-4)
    def testParseSearchResult(self):
        
        #nzbsorg
        with open("mock/nzbsorg_q_avengers_3results.xml") as f:
            entries = self.n1.process_query_result(f.read(), "aquery").entries
        self.assertEqual(3, len(entries))
        
        self.assertEqual(entries[0].title, "AVENGERS AGE OF ULTRON (2015)")
        assert entries[0].size == 2893890900
        assert entries[0].guid == "eff551fbdb69d6777d5030c209ee5d4b"
        self.assertEqual(entries[0].age_days, 1)
        self.assertEqual(entries[0].epoch, 1444584857)
        self.assertEqual(entries[0].pubdate_utc, "2015-10-11T17:34:17+00:00")
        self.assertEqual(entries[0].poster, "chuck@norris.com")
        self.assertEqual(entries[0].group, "alt.binaries.mom")
        
        self.assertEqual(entries[1].group, "alt.binaries.hdtv.x264")
        
        
        
    
    def testNewznabSearchQueries(self):
        
        self.args = SearchRequest(query="aquery")
        queries = self.n1.get_search_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=search" in query
        assert "q=aquery" in query
        
        self.args = SearchRequest(query=None)
        queries = self.n1.get_showsearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=tvsearch" in query
        
        self.args = SearchRequest(category="All")
        queries = self.n1.get_showsearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=tvsearch" in query
        
        self.args = SearchRequest(identifier_value="8511", identifier_key="rid")
        queries = self.n1.get_showsearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=tvsearch" in query
        assert "rid=8511" in query
        
        self.args = SearchRequest(identifier_value="8511", identifier_key="rid", season=1)
        queries = self.n1.get_showsearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=tvsearch" in query
        assert "rid=8511" in query
        assert "season=1" in query
        
        self.args = SearchRequest(identifier_value="8511", identifier_key="rid", season=1, episode=2)
        queries = self.n1.get_showsearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=tvsearch" in query
        assert "rid=8511" in query
        assert "season=1" in query
        assert "ep=2" in query
        
        self.args = SearchRequest(identifier_value="12345678", identifier_key="imdbid")
        queries = self.n1.get_moviesearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=movie" in query
        assert "imdbid=12345678" in query
        
        self.args = SearchRequest(identifier_value="12345678", identifier_key="imdbid", category="Movies")
        queries = self.n1.get_moviesearch_urls(self.args)
        assert len(queries) == 1
        query = queries[0]
        assert "http://127.0.0.1:5001/nzbsorg" in query
        assert "apikey=apikeynzbsorg" in query
        assert "t=movie" in query
        assert "imdbid=12345678" in query
        assert "cat=2000" in query
        
        
    @responses.activate
    def testGetNfo(self):
        with open("mock/dognzb--id-b4ba74ecb5f5962e98ad3c40c271dcc8--t-getnfo.xml", encoding="latin-1") as f:
            xml = f.read()
            
            url_re = re.compile(r'.*')
            responses.add(responses.GET, url_re,
                          body=xml, status=200,
                          content_type='application/x-html')
            nfo = self.n2.get_nfo("b4ba74ecb5f5962e98ad3c40c271dcc8")
            assert "Road Hard" in nfo
            
    @responses.activate
    def testOffsetStuff(self):
        
        
        mockitem_nzbs = []
        for i in range(100):
            mockitem_nzbs.append(mockbuilder.buildNewznabItem("myId", "myTitle", "myGuid", "http://nzbs.org/myId.nzb", None, None, 12345, "NZBs.org", [2000, 2040]))
        mockresponse_nzbs1 = mockbuilder.buildNewznabResponse("NZBs.org", mockitem_nzbs, offset=0, total=200)
        
        mockitem_nzbs.clear()
        for i in range(100):
            mockitem_nzbs.append(mockbuilder.buildNewznabItem("myId", "myTitle", "myGuid", "http://nzbs.org/myId.nzb", None, None, 12345, "NZBs.org", [2000, 2040]))
        mockresponse_nzbs2 = mockbuilder.buildNewznabResponse("NZBs.org", mockitem_nzbs, offset=100, total=200)

        r = self.n1.process_query_result(json.dumps(mockresponse_nzbs1), "http://127.0.0.1:5001/nzbsorg/q=whatever&offset=0&limit=0")
        further_queries = r.queries
        self.assertEqual(1, len(further_queries))
        assert "offset=100" in further_queries[0]
        
        r = self.n1.process_query_result(json.dumps(mockresponse_nzbs2), "http://127.0.0.1:5001/nzbsorg/q=whatever&offset=0&limit=0")
        further_queries = r.queries
        self.assertEqual(0, len(further_queries))
        
    
    def testGetNzbLink(self):
        link = self.n1.get_nzb_link("guid", None)
        assert "id=guid" in link
        assert "t=get" in link
        
    def testMapCats(self):
        from nzbhydra.searchmodules import newznab
        assert newznab.map_category("Movies") == [2000]
        assert newznab.map_category("2000") == [2000]
        newznabcats = newznab.map_category("2030,2040")
        assert len(newznabcats) == 2
        assert 2030 in newznabcats
        assert 2040 in newznabcats
import json
import re
import unittest

import mock
import pytest
import responses

from nzbhydra import infos
from nzbhydra.database import init_db, TvIdCache, MovieIdCache
from nzbhydra.infos import find_movie_ids, tmdbid_to_imdbid


class MyTestCase(unittest.TestCase):
    
    @pytest.fixture
    def setUp(self):
        tmdbConfigPatcher = mock.patch("tmdbsimple.Configuration.info")
        configMock = tmdbConfigPatcher.start()
        configMock.return_value = {"images": {"secure_base_url": "http://base.com/", "poster_sizes": ["w92"]}}
        
        tmdbSearchPatcher = mock.patch("tmdbsimple.Search.movie")
        self.searchMock = tmdbSearchPatcher.start()
        with open("mock/tmdb_search_response.json") as f:
            self.searchMock.return_value = json.load(f)
        
        tmdbFindPatcher = mock.patch("tmdbsimple.Find.info")
        self.findMock = tmdbFindPatcher.start()
        with open("mock/tmdb_imdbidsearch_response.json") as f:
            self.findMock.return_value = json.load(f)
        
        tmdbMoviesPatcher = mock.patch("tmdbsimple.Movies.info")
        self.moviesMock = tmdbMoviesPatcher.start()
        with open("mock/tmdb_movies_response.json") as f:
            self.moviesMock.return_value = json.load(f)
            
        with open("mock/tvmaze_search_response.json") as f:
            self.tvmazeSearchResponse = f.read()
        with open("mock/tvmaze_show_response.json") as f:
            self.tvmazeShowResponse = f.read()
        with open("mock/omdb_id_response.json") as f:
            self.omdbIdResponse = f.read()
                   

        init_db("tests.db")
        TvIdCache().delete().execute()

    

    def testFindMovieIds(self):
        infos = find_movie_ids("xyz")
        self.assertEqual(5, len(infos))
        first = infos[0]
        self.assertEqual("American Beauty", first["label"])
        self.assertEqual(u'http://base.com/w92/or1MP8BZIAjqWYxPdPX724ydKar.jpg', first["poster"])
        self.assertEqual(14, first["value"])

    def testTmdbToImdb(self):
        with open("mock/tmdb_id_response.json") as f:
            self.findMock.return_value = json.load(f)
        id = tmdbid_to_imdbid("14")
        self.assertEqual("0169547", id)   
        
    def testImdbToTmdb(self):
        with open("mock/tmdb_id_response.json") as f:
            self.searchMock.return_value = json.load(f)
        id = infos.imdbid_to_tmdbid("0169547")
        self.assertEqual("14", id)
            
    def testFindSeriesId(self):
        with responses.RequestsMock() as rsps:
            url_re = re.compile(r'http://api.tvmaze.com/search/shows\?q=breaking%20bad')
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeSearchResponse, status=200,
                     content_type='application/json')
            results = infos.find_series_ids("breaking bad")
            self.assertEqual(1, len(results))
            self.assertEqual("81189", results[0]["value"])
            self.assertEqual("Breaking Bad", results[0]["label"])
            self.assertEqual("http://tvmazecdn.com/uploads/images/medium_portrait/0/2400.jpg", results[0]["poster"])
            
    def testTitleFromId(self):
        with responses.RequestsMock() as rsps:
            url_re = re.compile(r"http://www.omdbapi.com/\?i=tt0169547&plot=short&r=json")
            rsps.add(responses.GET, url_re,
                     body=self.omdbIdResponse, status=200,
                     content_type='application/json')
            title = infos.title_from_id("imdbid", "0169547")
            self.assertEqual("American Beauty", title)
            
    
    def testConvert(self):
        TvIdCache.delete().execute()
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            url_re = re.compile(r'http://api.tvmaze.com/lookup/shows\?thetvdb=299350')
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvdb", "tvrage", "299350")
            self.assertEqual("47566", id)
            #This time from cache
            id = infos.convertId("tvdb", "tvrage", "299350")
            self.assertEqual("47566", id)
            
            TvIdCache.delete().execute()
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvdb", "tvmaze", "299350")
            self.assertEqual("3036", id)
            #This time from cache
            id = infos.convertId("tvdb", "tvmaze", "299350")
            self.assertEqual("3036", id)

        TvIdCache.delete().execute()
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            url_re = re.compile(r'http://api.tvmaze.com/lookup/shows\?tvrage=47566')
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvrage", "tvdb", "47566")
            self.assertEqual("299350", id)
            
            TvIdCache.delete().execute()
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvrage", "tvmaze", "47566")
            self.assertEqual("3036", id)
        
        TvIdCache.delete().execute()
        with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
            url_re = re.compile(r'http://api.tvmaze.com/shows/3036')
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvmaze", "tvrage", "3036")
            self.assertEqual("47566", id)
            
            TvIdCache.delete().execute()
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            id = infos.convertId("tvmaze", "tvdb", "3036")
            self.assertEqual("299350", id)
        
        MovieIdCache.delete().execute()
        with open("mock/tmdb_id_response.json") as f:
            self.searchMock.return_value = json.load(f)
        MovieIdCache.delete().execute()
        id = infos.convertId("imdb", "tmdb", "0169547")
        self.assertEqual("14", id)
        #This time from cache
        id = infos.convertId("imdb", "tmdb", "0169547")
        self.assertEqual("14", id)
        
        MovieIdCache.delete().execute()
        with open("mock/tmdb_id_response.json") as f:
            self.searchMock.return_value = json.load(f)
        MovieIdCache.delete().execute()
        id = infos.convertId("tmdb", "imdb", "14")
        self.assertEqual("0169547", id)

    def testCanConvertList(self):
        self.assertTrue(infos.canConvertList("tvrage", ["tvdb", "tvmaze"]))
        self.assertTrue(infos.canConvertList("tvdb", ["tvrage", "tvmaze"]))
        self.assertTrue(infos.canConvertList("tvmaze", ["tvrage", "tvdbid"]))
        self.assertTrue(infos.canConvertList("imdb", ["tmdb"]))
        self.assertTrue(infos.canConvertList("tmdb", ["imdb"]))
        
    def testConvertToAny(self):
        with responses.RequestsMock() as rsps:
            url_re = re.compile(r'http://api.tvmaze.com/shows/3036')
            rsps.add(responses.GET, url_re,
                     body=self.tvmazeShowResponse, status=200,
                     content_type='application/json')
            canConvert, toType, id = infos.convertIdToAny("tvmaze", ["rid", "tvdb"], "3036")
            self.assertTrue(canConvert)
            self.assertEqual(toType, "tvrage")
            self.assertEqual("47566", id)

            canConvert, toType, id = infos.convertIdToAny("tvrage", ["tvmaze", "tvdb"], "47566")
            self.assertTrue(canConvert)
            self.assertEqual(toType, "tvmaze")
            self.assertEqual("3036", id)

            canConvert, toType, id = infos.convertIdToAny("tvrage", ["tvdbid", "tvmazeid"], "47566")
            self.assertTrue(canConvert)
            self.assertEqual(toType, "tvdb")
            self.assertEqual("299350", id)

            canConvert, toType, id = infos.convertIdToAny("tvmaze", ["imdbid", "tmdb"], "3036")
            self.assertFalse(canConvert)

        with open("mock/tmdb_id_response.json") as f:
            self.searchMock.return_value = json.load(f)
            canConvert, toType, id = infos.convertIdToAny("imdb", ["tmdbid"], "0169547")
        self.assertTrue(canConvert)
        self.assertEqual(toType, "tmdb")

        self.searchMock.reset_mock()
        canConvert, toType, id = infos.convertIdToAny("imdb", ["imdb"], "0169547")
        self.assertTrue(canConvert)
        self.assertEqual(toType, "imdb")
        self.assertEqual("0169547", id)
        self.assertFalse(self.searchMock.called)

        self.searchMock.reset_mock()
        canConvert, toType, id = infos.convertIdToAny("imdb", "imdb", "0169547") #Single ID instead of list
        self.assertTrue(canConvert)
        self.assertEqual(toType, "imdb")
        self.assertEqual("0169547", id)
        self.assertFalse(self.searchMock.called)
            
            
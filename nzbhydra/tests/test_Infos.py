import json
import re
import unittest

import mock
import pytest
import responses
import vcr

from nzbhydra import infos
from nzbhydra.database import init_db, TvIdCache, MovieIdCache
from nzbhydra.infos import find_movie_ids, tmdbid_to_imdbid


class TestInfos(unittest.TestCase):
    
    @pytest.fixture
    def setUp(self):
        init_db("tests.db")
        TvIdCache().delete().execute()

    @vcr.use_cassette('vcr/tmdb.yaml', record_mode='once')
    def testFindMovieIds(self):
        infos = find_movie_ids("American Beauty")
        self.assertEqual(5, len(infos))
        first = infos[0]
        self.assertEqual("American Beauty", first["title"])
        self.assertEqual("American Beauty (1999)", first["label"])
        self.assertEqual(u'https://image.tmdb.org/t/p/w92/or1MP8BZIAjqWYxPdPX724ydKar.jpg', first["poster"])
        self.assertEqual(14, first["value"])

    @vcr.use_cassette('vcr/tmdb.yaml', record_mode='once')
    def testTmdbToImdb(self):
        id = tmdbid_to_imdbid("14")
        self.assertEqual("0169547", id)

    @vcr.use_cassette('vcr/tmdb.yaml', record_mode='once')
    def testImdbToTmdb(self):
        id = infos.imdbid_to_tmdbid("0169547")
        self.assertEqual("14", id)

    @vcr.use_cassette('vcr/tvmaze.yaml', record_mode='once')
    def testFindSeriesId(self):
        results = infos.find_series_ids("breaking bad")
        self.assertEqual(1, len(results))
        self.assertEqual("81189", results[0]["value"])
        self.assertEqual("Breaking Bad", results[0]["label"])
        self.assertEqual("http://tvmazecdn.com/uploads/images/medium_portrait/0/2400.jpg", results[0]["poster"])

    @vcr.use_cassette('vcr/omdb.yaml', record_mode='once')
    def testTitleFromId(self):
        title = infos.title_from_id("imdbid", "0169547")
        self.assertEqual("American Beauty", title)

    @vcr.use_cassette('vcr/tvmaze.yaml', record_mode='once')
    def testConvertTv(self):
        TvIdCache.delete().execute()
        id = infos.convertId("tvdb", "tvrage", "299350")
        self.assertEqual("47566", id)
        #This time from cache
        id = infos.convertId("tvdb", "tvrage", "299350")
        self.assertEqual("47566", id)
        
        TvIdCache.delete().execute()
        
        id = infos.convertId("tvdb", "tvmaze", "299350")
        self.assertEqual("3036", id)
        #This time from cache
        id = infos.convertId("tvdb", "tvmaze", "299350")
        self.assertEqual("3036", id)

        TvIdCache.delete().execute()
        id = infos.convertId("tvrage", "tvdb", "47566")
        self.assertEqual("299350", id)
        
        TvIdCache.delete().execute()
        id = infos.convertId("tvrage", "tvmaze", "47566")
        self.assertEqual("3036", id)
        
        TvIdCache.delete().execute()
        id = infos.convertId("tvmaze", "tvrage", "3036")
        self.assertEqual("47566", id)
        
        TvIdCache.delete().execute()
        id = infos.convertId("tvmaze", "tvdb", "3036")
        self.assertEqual("299350", id)

    @vcr.use_cassette('vcr/tmdb.yaml', record_mode='once')
    def testConvertMovie(self):
        MovieIdCache.delete().execute()
        id = infos.convertId("imdb", "tmdb", "0169547")
        self.assertEqual("14", id)
        #This time from cache
        id = infos.convertId("imdb", "tmdb", "0169547")
        self.assertEqual("14", id)
        
        MovieIdCache.delete().execute()
        id = infos.convertId("tmdb", "imdb", "14")
        self.assertEqual("0169547", id)

    def testCanConvertList(self):
        self.assertTrue(infos.canConvertList("tvrage", ["tvdb", "tvmaze"]))
        self.assertTrue(infos.canConvertList("tvdb", ["tvrage", "tvmaze"]))
        self.assertTrue(infos.canConvertList("tvmaze", ["tvrage", "tvdbid"]))
        self.assertTrue(infos.canConvertList("imdb", ["tmdb"]))
        self.assertTrue(infos.canConvertList("tmdb", ["imdb"]))

    @vcr.use_cassette('vcr/tvmaze.yaml', record_mode='once')
    def testConvertToAny(self):
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

    @vcr.use_cassette('vcr/tmdb.yaml', record_mode='once')
    def testConvertToAny(self):
        canConvert, toType, id = infos.convertIdToAny("imdb", ["tmdbid"], "0169547")
        self.assertTrue(canConvert)
        self.assertEqual(toType, "tmdb")

        canConvert, toType, id = infos.convertIdToAny("imdb", ["imdb"], "0169547")
        self.assertTrue(canConvert)
        self.assertEqual(toType, "imdb")
        self.assertEqual("0169547", id)

        canConvert, toType, id = infos.convertIdToAny("imdb", "imdb", "0169547") #Single ID instead of list
        self.assertTrue(canConvert)
        self.assertEqual(toType, "imdb")
        self.assertEqual("0169547", id)
            
            
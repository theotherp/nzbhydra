#!/usr/bin/python
from __future__ import unicode_literals

import json
import re
from datetime import datetime

from pytvmaze import endpoints
from pytvmaze.exceptions import *

try:
    # Python 3 and later
    from urllib.request import urlopen
    from urllib.parse import quote as url_quote, unquote as url_unquote
    from urllib.error import URLError, HTTPError
except ImportError:
    # Python 2
    from urllib2 import urlopen, URLError, HTTPError
    from urllib import quote as url_quote, unquote as url_unquote


def _valid_encoding(text):
    if not text:
        return
    if sys.version_info > (3,):
        return text
    else:
        return unicode(text).encode('utf-8')


class Show(object):
    def __init__(self, data):
        self.status = data.get('status')
        self.rating = data.get('rating')
        self.genres = data.get('genres')
        self.weight = data.get('weight')
        self.updated = data.get('updated')
        self.name = data.get('name')
        self.language = data.get('language')
        self.schedule = data.get('schedule')
        self.url = data.get('url')
        self.image = data.get('image')
        self.externals = data.get('externals')
        self.premiered = data.get('premiered')
        self.summary = _remove_tags(data.get('summary'))
        self.links = data.get('_links')
        self.web_channel = data.get('webChannel')
        self.runtime = data.get('runtime')
        self.type = data.get('type')
        self.id = data.get('id')
        self.maze_id = self.id
        self.network = data.get('network')
        self.episodes = list()
        self.seasons = dict()
        self.cast = None
        self.populate(data)

    def __repr__(self):
        if self.premiered:
            year = str(self.premiered[:4])
        else:
            year = None
        if self.web_channel:
            platform = ',show_web_channel='
            network = self.web_channel.get('name')
        elif self.network:
            platform = ',network='
            network = self.network.get('name')
        else:
            platform = ''
            network = ''

        return _valid_encoding('<Show(maze_id={id},name={name},year={year}{platform}{network})>'.format(
                id=self.maze_id,
                name=self.name,
                year=year,
                platform=platform,
                network=network)
        )

    def __str__(self):
        return _valid_encoding(self.name)

    def __unicode__(self):
        return self.name

    def __iter__(self):
        return iter(self.seasons.values())

    # Python 3 bool evaluation
    def __bool__(self):
        return bool(self.id)

    # Python 2 bool evaluation
    def __nonzero__(self):
        return bool(self.id)

    def __len__(self):
        return len(self.seasons)

    def __getitem__(self, item):
        try:
            return self.seasons[item]
        except KeyError:
            raise SeasonNotFound('Season {0} does not exist for show {1}.'.format(item, self.name))

    def populate(self, data):
        embedded = data.get('_embedded')
        if embedded:
            if embedded.get('episodes'):
                seasons = show_seasons(self.maze_id)
                for episode in embedded.get('episodes'):
                    self.episodes.append(Episode(episode))
                for episode in self.episodes:
                    season_num = int(episode.season_number)
                    if season_num not in self.seasons:
                        self.seasons[season_num] = seasons[season_num]
                        self.seasons[season_num].show = self
                    self.seasons[season_num].episodes[episode.episode_number] = episode
            if embedded.get('cast'):
                self.cast = Cast(embedded.get('cast'))


class Season(object):
    def __init__(self, data):
        self.show = None
        self.episodes = dict()
        self.id = data.get('id')
        self.url = data.get('url')
        self.season_number = data.get('number')
        self.name = data.get('name')
        self.episode_order = data.get('episodeOrder')
        self.premier_date = data.get('premierDate')
        self.end_date = data.get('endDate')
        self.network = data.get('network')
        self.web_channel = data.get('webChannel')
        self.image = data.get('image')
        self.summary = data.get('summary')
        self.links = data.get('_links')

    def __repr__(self):
        return _valid_encoding('<Season(id={id},season_number={number})>'.format(
                id=self.id,
                number=str(self.season_number).zfill(2)
        ))

    def __iter__(self):
        return iter(self.episodes.values())

    def __len__(self):
        return len(self.episodes)

    def __getitem__(self, item):
        try:
            return self.episodes[item]
        except KeyError:
            raise EpisodeNotFound(
                    'Episode {0} does not exist for season {1} of show {2}.'.format(item, self.season_number,
                                                                                    self.show))

    # Python 3 bool evaluation
    def __bool__(self):
        return bool(self.id)

    # Python 2 bool evaluation
    def __nonzero__(self):
        return bool(self.id)

class Episode(object):
    def __init__(self, data):
        self.title = data.get('name')
        self.airdate = data.get('airdate')
        self.url = data.get('url')
        self.season_number = data.get('season')
        self.episode_number = data.get('number')
        self.image = data.get('image')
        self.airstamp = data.get('airstamp')
        self.airtime = data.get('airtime')
        self.runtime = data.get('runtime')
        self.summary = _remove_tags(data.get('summary'))
        self.maze_id = data.get('id')
        # Reference to show for when using get_schedule()
        if data.get('show'):
            self.show = Show(data.get('show'))
        # Reference to show for when using get_full_schedule()
        if data.get('_embedded'):
            if data['_embedded'].get('show'):
                self.show = Show(data['_embedded']['show'])

    def __repr__(self):
        return '<Episode(season={season},episode_number={number})>'.format(
                season=str(self.season_number).zfill(2),
                number=str(self.episode_number).zfill(2)
        )

    def __str__(self):
        season = 'S' + str(self.season_number).zfill(2)
        episode = 'E' + str(self.episode_number).zfill(2)
        return _valid_encoding(season + episode + ' ' + self.title)


class Person(object):
    def __init__(self, data):
        if data.get('person'):
            data = data['person']
        self.links = data.get('_links')
        self.id = data.get('id')
        self.image = data.get('image')
        self.name = data.get('name')
        self.score = data.get('score')
        self.url = data.get('url')
        self.character = None
        self.castcredits = None
        self.crewcredits = None
        self.populate(data)

    def populate(self, data):
        if data.get('_embedded'):
            if data['_embedded'].get('castcredits'):
                self.castcredits = [CastCredit(credit)
                                    for credit in data['_embedded']['castcredits']]
            elif data['_embedded'].get('crewcredits'):
                self.crewcredits = [CrewCredit(credit)
                                    for credit in data['_embedded']['crewcredits']]

    def __repr__(self):
        return _valid_encoding('<Person(name={name},maze_id={id})>'.format(
                name=self.name,
                id=self.id
        ))

    def __str__(self):
        return _valid_encoding(self.name)


class Character(object):
    def __init__(self, data):
        self.id = data.get('id')
        self.url = data.get('url')
        self.name = data.get('name')
        self.image = data.get('image')
        self.links = data.get('_links')
        self.person = None

    def __repr__(self):
        return _valid_encoding('<Character(name={name},maze_id={id})>'.format(
                name=self.name,
                id=self.id
        ))

    def __str__(self):
        return _valid_encoding(self.name)

    def __unicode__(self):
        return self._repr_obj(as_unicode=True)


class Cast(object):
    def __init__(self, data):
        self.people = []
        self.characters = []
        self.populate(data)

    def populate(self, data):
        for cast_member in data:
            self.people.append(Person(cast_member['person']))
            self.characters.append(Character(cast_member['character']))
            self.people[-1].character = self.characters[-1]  # add reference to character
            self.characters[-1].person = self.people[-1]  # add reference to cast member


class CastCredit(object):
    def __init__(self, data):
        self.links = data.get('_links')
        self.character = None
        self.show = None
        self.populate(data)

    def populate(self, data):
        if data.get('_embedded'):
            if data['_embedded'].get('character'):
                self.character = Character(data['_embedded']['character'])
            elif data['_embedded'].get('show'):
                self.show = Show(data['_embedded']['show'])


class CrewCredit(object):
    def __init__(self, data):
        self.links = data.get('_links')
        self.type = data.get('type')
        self.show = None
        self.populate(data)

    def populate(self, data):
        if data.get('_embedded'):
            if data['_embedded'].get('show'):
                self.show = Show(data['_embedded']['show'])


class Updates(object):
    def __init__(self, data):
        self.updates = dict()
        self.populate(data)

    def populate(self, data):
        for maze_id, time in data.items():
            self.updates[int(maze_id)] = Update(maze_id, time)

    def __getitem__(self, item):
        try:
            return self.updates[item]
        except KeyError:
            raise UpdateNotFound('No update found for Maze id {}.'.format(item))


class Update(object):
    def __init__(self, maze_id, time):
        self.maze_id = int(maze_id)
        self.seconds_since_epoch = time
        self.timestamp = datetime.fromtimestamp(time)

    def __repr__(self):
        return '<Update(maze_id={maze_id},time={time})>'.format(
                maze_id=self.maze_id,
                time=self.seconds_since_epoch
        )


class AKA(object):
    def __init__(self, data):
        self.country = data.get('country')
        self.name = data.get('name')


def _remove_tags(text):
    return re.sub(r'<.*?>', '', text)


# Query TV Maze endpoints
def _query_endpoint(url):
    try:
        data = urlopen(url).read()
    except HTTPError as e:
        if e.code in [404, 422]:
            return None
        elif e.code == 400:
            raise BadRequest(e.reason + ' ' + str(e.code) + ' ' + e.url)
    except URLError as e:
        raise ConnectionError(repr(e))

    try:
        results = json.loads(data)
    except:
        results = json.loads(data.decode('utf8'))

    if results:
        return results
    else:
        return None


# Get Show object
def get_show(maze_id=None, tvdb_id=None, tvrage_id=None, imdb_id=None, show_name=None,
             show_year=None, show_network=None, show_language=None,
             show_country=None, show_web_channel=None, embed=None):
    """
    Get Show object directly via id or indirectly via name + optional qualifiers

    If only a show_name is given, the show with the highest score using the
    tvmaze algorithm will be returned.
    If you provide extra qualifiers such as network or language they will be
    used for a more specific match, if one exists.
    :param maze_id: Show maze_id
    :param tvdb_id: Show tvdb_id
    :param tvrage_id: Show tvrage_id
    :param show_name: Show name to be searched
    :param show_year: Show premiere year
    :param show_network: Show TV Network (like ABC, NBC, etc.)
    :param show_web_channel: Show Web Channel (like Netflix, Amazon, etc.)
    :param show_language: Show language
    :param show_country: Show country
    :param embed: embed parameter to include additional data. Currently 'episodes' and 'cast' are supported
    :return:
    """
    errors = []
    if not (maze_id or tvdb_id or tvrage_id or imdb_id or show_name):
        raise MissingParameters(
                'Either maze_id, tvdb_id, tvrage_id, imdb_id or show_name are required to get show, none provided,')
    if maze_id:
        try:
            return show_main_info(maze_id, embed=embed)
        except IDNotFound as e:
            errors.append(e.value)
    if tvdb_id:
        try:
            return show_main_info(lookup_tvdb(tvdb_id).id, embed=embed)
        except IDNotFound as e:
            errors.append(e.value)
    if tvrage_id:
        try:
            return show_main_info(lookup_tvrage(tvrage_id).id, embed=embed)
        except IDNotFound as e:
            errors.append(e.value)
    if imdb_id:
        try:
            return show_main_info(lookup_imdb(imdb_id).id, embed=embed)
        except IDNotFound as e:
            errors.append(e.value)
    if show_name:
        try:
            show = _get_show_by_search(show_name, show_year, show_network, show_language, show_country,
                                       show_web_channel, embed=embed)
            return show
        except ShowNotFound as e:
            errors.append(e.value)
    raise ShowNotFound(' ,'.join(errors))


def _get_show_with_qualifiers(show_name, qualifiers):
    shows = get_show_list(show_name)
    best_match = -1  # Initialize match value score
    show_match = None

    for show in shows:
        if show.premiered:
            premiered = show.premiered[:-6].lower()
        else:
            premiered = None
        if show.network:
            network = show.network['name'].lower()
        else:
            network = None
        if show.web_channel:
            web_channel = show.web_channel['name'].lower()
        else:
            web_channel = None
        if show.network:
            country = show.network['country']['code'].lower()
        else:
            if show.web_channel:
                country = show.web_channel['country']['code'].lower()
            else:
                country = None
        if show.language:
            language = show.language.lower()
        else:
            language = None

        attributes = [premiered, country, network, language, web_channel]
        show_score = len(set(qualifiers) & set(attributes))
        if show_score > best_match:
            best_match = show_score
            show_match = show
    return show_match


# Search with user-defined qualifiers, used by get_show() method
def _get_show_by_search(show_name, show_year, show_network, show_language, show_country, show_web_channel, embed):
    if show_year:
        show_year = str(show_year)
    qualifiers = filter(None, [show_year, show_network, show_language, show_country, show_web_channel])
    if qualifiers:
        qualifiers = [q.lower() for q in qualifiers if q]
        show = _get_show_with_qualifiers(show_name, qualifiers)
    else:
        return show_single_search(show=show_name, embed=embed)
    if embed:
        return show_main_info(maze_id=show.id, embed=embed)
    else:
        return show


def _url_quote(show):
    return url_quote(show.encode('UTF-8'))


# Return list of Show objects
def get_show_list(show_name):
    """
    Return list of Show objects from the TVMaze "Show Search" endpoint

    List will be ordered by tvmaze score and should mimic the results you see
    by doing a show search on the website.
    :param show_name: Name of show
    :return: List of Show(s)
    """
    shows = show_search(show_name)
    return shows


# Get list of Person objects
def get_people(name):
    """
    Return list of Person objects from the TVMaze "People Search" endpoint
    :param name: Name of person
    :return: List of Person(s)
    """
    people = people_search(name)
    if people:
        return people


# TV Maze Endpoints
def show_search(show):
    _show = _url_quote(show)
    url = endpoints.show_search.format(_show)
    q = _query_endpoint(url)
    if q:
        return [Show(show['show']) for show in q]
    else:
        raise ShowNotFound('Show {0} not found'.format(show))


def show_single_search(show, embed=None):
    _show = _url_quote(show)
    if embed:
        url = endpoints.show_single_search.format(_show) + '&embed=' + embed
    else:
        url = endpoints.show_single_search.format(_show)
    q = _query_endpoint(url)
    if q:
        return Show(q)
    else:
        raise ShowNotFound('show name "{0}" not found'.format(show))


def lookup_tvrage(tvrage_id):
    url = endpoints.lookup_tvrage.format(tvrage_id)
    q = _query_endpoint(url)
    if q:
        return Show(q)
    else:
        raise IDNotFound('TVRage id {0} not found'.format(tvrage_id))


def lookup_tvdb(tvdb_id):
    url = endpoints.lookup_tvdb.format(tvdb_id)
    q = _query_endpoint(url)
    if q:
        return Show(q)
    else:
        raise IDNotFound('TVDB ID {0} not found'.format(tvdb_id))


def lookup_imdb(imdb_id):
    url = endpoints.lookup_imdb.format(imdb_id)
    q = _query_endpoint(url)
    if q:
        return Show(q)
    else:
        raise IDNotFound('IMDB ID {0} not found'.format(imdb_id))


def get_schedule(country='US', date=str(datetime.today().date())):
    url = endpoints.get_schedule.format(country, date)
    q = _query_endpoint(url)
    if q:
        return [Episode(episode) for episode in q]
    else:
        raise ScheduleNotFound('Schedule for country {0} at date {1} not found'.format(country, date))


# ALL known future episodes, several MB large, cached for 24 hours
def get_full_schedule():
    url = endpoints.get_full_schedule
    q = _query_endpoint(url)
    if q:
        return [Episode(episode) for episode in q]
    else:
        raise GeneralError('Something went wrong, www.tvmaze.com may be down')


def show_main_info(maze_id, embed=None):
    if embed:
        url = endpoints.show_main_info.format(maze_id) + '?embed=' + embed
    else:
        url = endpoints.show_main_info.format(maze_id)
    q = _query_endpoint(url)
    if q:
        return Show(q)
    else:
        raise IDNotFound('Maze id {0} not found'.format(maze_id))


def episode_list(maze_id, specials=None):
    if specials:
        url = endpoints.episode_list.format(maze_id) + '&specials=1'
    else:
        url = endpoints.episode_list.format(maze_id)
    q = _query_endpoint(url)
    if q:
        return [Episode(episode) for episode in q]
    else:
        raise IDNotFound('Maze id {0} not found'.format(maze_id))


def episode_by_number(maze_id, season_number, episode_number):
    url = endpoints.episode_by_number.format(maze_id,
                                             season_number,
                                             episode_number)
    q = _query_endpoint(url)
    if q:
        return Episode(q)
    else:
        raise EpisodeNotFound(
                'Couldn\'t find season {0} episode {1} for TVMaze ID {2}'.format(season_number, episode_number,
                                                                                 maze_id))


def episodes_by_date(maze_id, airdate):
    try:
        datetime.strptime(airdate, '%Y-%m-%d')
    except ValueError:
        raise IllegalAirDate('Airdate must be string formatted as \"YYYY-MM-DD\"')
    url = endpoints.episodes_by_date.format(maze_id, airdate)
    q = _query_endpoint(url)
    if q:
        return [Episode(episode) for episode in q]
    else:
        raise NoEpisodesForAirdate(
                'Couldn\'t find an episode airing {0} for TVMaze ID {1}'.format(airdate, maze_id))


def show_cast(maze_id):
    url = endpoints.show_cast.format(maze_id)
    q = _query_endpoint(url)
    if q:
        return Cast(q)
    else:
        raise CastNotFound('Couldn\'nt find show cast for TVMaze ID {0}'.format(maze_id))


def show_index(page=1):
    url = endpoints.show_index.format(page)
    q = _query_endpoint(url)
    if q:
        return [Show(show) for show in q]
    else:
        raise ShowIndexError('Error getting show index, www.tvmaze.com may be down')


def people_search(person):
    person = _url_quote(person)
    url = endpoints.people_search.format(person)
    q = _query_endpoint(url)
    if q:
        return [Person(person) for person in q]
    else:
        raise PersonNotFound('Couldn\'t find person: {0}'.format(person))


def person_main_info(person_id, embed=None):
    if embed:
        url = endpoints.person_main_info.format(person_id) + '?embed=' + embed
    else:
        url = endpoints.person_main_info.format(person_id)
    q = _query_endpoint(url)
    if q:
        return Person(q)
    else:
        raise PersonNotFound('Couldn\'t find person: {0}'.format(person_id))


def person_cast_credits(person_id, embed=None):
    if embed:
        url = endpoints.person_cast_credits.format(person_id) + '?embed=' + embed
    else:
        url = endpoints.person_cast_credits.format(person_id)
    q = _query_endpoint(url)
    if q:
        return [CastCredit(credit) for credit in q]
    else:
        raise CreditsNotFound('Couldn\'t find cast credits for person ID: {0}'.format(person_id))


def person_crew_credits(person_id, embed=None):
    if embed:
        url = endpoints.person_crew_credits.format(person_id) + '?embed=' + embed
    else:
        url = endpoints.person_crew_credits.format(person_id)
    q = _query_endpoint(url)
    if q:
        return [CrewCredit(credit) for credit in q]
    else:
        raise CreditsNotFound('Couldn\'t find crew credits for person ID: {0}'.format(person_id))


def show_updates():
    url = endpoints.show_updates
    q = _query_endpoint(url)
    if q:
        return Updates(q)
    else:
        raise ShowIndexError('Error getting show updates, www.tvmaze.com may be down')


def show_akas(maze_id):
    url = endpoints.show_akas.format(maze_id)
    q = _query_endpoint(url)
    if q:
        return [AKA(aka) for aka in q]
    else:
        raise AKASNotFound('Couldn\'t find AKA\'s for TVMaze ID: {0}'.format(maze_id))


def show_seasons(maze_id):
    url = endpoints.show_seasons.format(maze_id)
    q = _query_endpoint(url)
    if q:
        season_dict = dict()
        for season in q:
            season_dict[season['number']] = Season(season)
        return season_dict
    else:
        raise SeasonNotFound('Couldn\'t find Season\'s for TVMaze ID: {0}'.format(maze_id))


def season_by_id(season_id):
    url = endpoints.season_by_id.format(season_id)
    q = _query_endpoint(url)
    if q:
        return Season(q)
    else:
        raise SeasonNotFound('Couldn\'t find Season with ID: {0}'.format(season_id))

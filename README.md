# nzbhydra  [![Build Status](https://travis-ci.org/theotherp/nzbhydra.svg?branch=master)](https://travis-ci.org/theotherp/nzbhydra) [![Average time to resolve an issue](http://isitmaintained.com/badge/resolution/theotherp/nzbhydra.svg)](http://isitmaintained.com/project/theotherp/nzbhydra "Average time to resolve an issue") 
NZBHydra is a meta search for NZB indexers and the "spiritual successor" to [NZBmegasearcH](https://github.com/pillone/usntssearch). It provides easy access to a number of raw and newznab based indexers.


## Features
* Searches Binsearch, NZBIndex, NZBClub, omgwtfnzbs.org, Womble and most newznab compatible indexers (see https://github.com/theotherp/nzbhydra/issues/20 and https://github.com/theotherp/nzbhydra/wiki/Supported-Search-Types-And-Indexer-Hosts )
* Search by IMDB, TMDB, TVDB, TVRage and TVMaze ID (including season and episode) and filter by age and size. If an ID is not supported by an indexer it is attempted to be converted (e.g. TMDB to IMDB)
* Rudimentary (for now) query generation, meaning when you search for a movie using e.g. an IMDB ID a query will be generated for raw indexers. Searching for a series season 1 episode 2 will also generate queries for raw indexers, like s01e02 and 1x02
* Grouping of results with the same title and of duplicate results, accounting for result posting time, size, group and poster. By default only one of the duplicates is shown. You can provide an indexer score to influence which one that might be.
* Mostly compatible with newznab search API (tested with Sonarr, CP and NZB 360).
* Either proxy the NZBs from the indexers (keeping all X-NZB headers), redirect or use direct links in search results
* Included function to add results (single or a bunch) to SABnzbd or NZBGet(v13+) and show NFOs where available. Option to decide if links are added as links or the NZBs are uploaded. Select category in GUI or define a default.
* Statistics on indexers (average response time, share of results, access errors), NZB download history and search history (both via internal GUI and API). Indexers with problems are paused for an increasing time span (like in sonarr)
* Reverse proxy compatible. See https://github.com/theotherp/nzbhydra/wiki/Reverse-proxy
* See https://imgur.com/a/lBq9n for screenshots

##  How to run
Run with Python 2.7.9+. Runs on http://0.0.0.0:5075 by default. See the console output on how to choose the port and host using command line parameters.

## Running in Docker Container
Note: This was not done by me (TheOtherP) and I cannot provide support. Included with the source is build is a Dockerfile and a Docker Compose template to run this project within a Docker container. Prerequisites is to have Docker installed. If you'd like to run this within Docker Compose, you will need to have that installed as well. All of the following instructions for Docker assume you are in the root directory of this project.

### Building the container

#### Using Docker
- Run `$ docker build -t nzbhydra .`

#### Using Docker Compose
- Run `$ docker-compose build`
- **Note** that if you're using Docker Compose, there's no need to go through this step since running `docker-compose up` in the 'Running the container' step will also build the container in the same step.

### Running the container

#### Using Docker
- Run `$ docker run nzbhydra`

#### Using Docker Compose
- Run `$ docker-compose up`

Once the container is up and running you should see output like the following:
```
Loading settings from settings.cfg
2015-12-19 23:50:37,113 - INFO - nzbhydra - Started
2015-12-19 23:50:37,114 - INFO - nzbhydra - Loading database file nzbhydra.db
2015-12-19 23:50:37,115 - INFO - database - Initializing database and creating tables
2015-12-19 23:50:37,135 - INFO - database - Created new version info entry with database version 1
2015-12-19 23:50:37,137 - INFO - indexers - Loading indexer Binsearch
2015-12-19 23:50:37,138 - INFO - indexers - Unable to find indexer with name Binsearch in database. Will add it
[...]
2015-12-19 23:50:37,162 - INFO - nzbhydra - Starting web app on 0.0.0.0:5075
2015-12-19 23:50:37,163 - INFO - nzbhydra - Go to http://127.0.0.1:5075 for the frontend (or whatever your public IP is)
2015-12-19 23:50:37,416 - INFO - web - Using memory based cache
```

At this point NZBHydra is running. If you are not using boot2docker or docker-machine, you should be able to go to [http://127.0.0.1:5075](http://127.0.0.1:5075) and interact with the UI.

If you are on a Windows or Mac and are using docker-machine or boot2docker (usually installed via Docker Toolbox), you will need to get the IP for that VM and go to that IP in the browser.

More information about getting the docker-machine IP is available [here](https://docs.docker.com/machine/reference/ip/). If using boot2docker, the command to find the ip is `$ boot2docker ip`

## TODO
* A lot of bug fixing and improvements regarding performance and stability
* Better query generation
* More stats
* More indexers? Again, see ( https://github.com/theotherp/nzbhydra/issues/20 )
* Include comments, rating, etc or link to them
* Clean up code base


## To note
As I said query generation is very basic. When selecting a category and doing a search the category will only be used for newznab indexers, for all the raw indexers we will just search using the query. Generating "proper" queries from a category is very hard so you will need to do the filtering visually. Especially with raw indexers that don't support "OR" queries we would need to send a lot of requests to get all the different combinations

Newznab providers don't send information on NFO availablity. If the search results show an NFO link for such an indexer you will need to just try if you can get one.

Not all newznab indexers support search by imdbid, tvdbid and rageid. I added presets for common indexers. If you find an error or know the supported IDs and the indexer's host please let me know.

Currently the config GUI does not provide any validation apart from the connection tests.

The perfomance could / needs to be improved. Searches can easily take 20 seconds although they're executed in parallel. This is mainly due to the parsing of search results from indexers like NZBIndex being slow, but also due to some problems in the code which I don't really understand so far.

The program is currently in very early alpha. Upgrading to an new version might cause loss of the configuration, stats or history. The console will contain debug information. It will crash. It is definitely not ready for general use.

## Development and how you can help
Generally testing and any bug reports are very welcome.

Any pull requests are also welcome, but I feel I and the program would mostly profit from:
* Advice regarding stability, error handling, net code (I program Java by day and it shows) and performance (see above)
* More indexers (see above)

### Contact ###
Send me an email at TheOtherP@gmx.de or a PM at https://www.reddit.com/user/TheOtherP

### Donate ###
If you like to help me with any running or upcoming costs you're welcome to send money to my bitcoin: 13x4cfm5BNzedsSqdPcexUhAF3cP8LYrsk 

### License ###
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

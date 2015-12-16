# nzbhydra
NZBHydra is a meta search for NZB indexers and the "spiritual successor" to [NZBmegasearcH](https://github.com/pillone/usntssearch). It provides easy access to a number of raw and newznab based indexers.


##Features
* Searches Binsearch, NZBClub, NZBIndex, NZBClub, omgwtfnzbs.org, Womble and most newznab compatible indexers (see https://github.com/theotherp/nzbhydra/issues/20 and https://github.com/theotherp/nzbhydra/wiki/Supported-Search-Types-And-Indexer-Hosts )
* Search by IMDB, TVDB and TVRage ID (including season and episode) and filter by age and size
* Rudimentary (for now) query generation, meaning when you search for a movie using e.g. an IMDB ID a query will be generated for raw indexers. Searching for a series season 1 episode 2 will also generate queries for raw indexers, like s01e02 and 1x02
* Grouping of results with the same title and of duplicate results, accounting for result posting time, size, group and poster. By default only one of the duplicates is shown. You can provide an indexer score to influence which one that might be.
* Mostly compatible with newznab search API (tested with Sonarr, CP and NZB 360).
* Either proxy the NZBs from the indexers (keeping all X-NZB headers), redirect or use direct links in search results
* Included function to add results (single or a bunch) to SABnzbd or NZBGet(v13+) and show NFOs where available. Option to decide if links are added as links or the NZBs are uploaded. Select category in GUI or define a default.
* Statistics on indexers (average response time, share of results, access errors), NZB download history and search history (both via internal GUI and API). Indexers with problems are paused for an increasing time span (like in sonarr)
* Reverse proxy compatible without further configuration (tested with Apache) as long as the host is preserved. If you want to access the API from outside you may need to set the "Base URL" setting.
* A GUI that looks like ass
* See http://i.imgur.com/d53cmM7.png http://i.imgur.com/2DpXtxM.png http://i.imgur.com/uk9zwZB.png http://i.imgur.com/M0Pxy2F.png for screenshots

##How to run
Run with Python 2.7. Runs on http://0.0.0.0:5075 by default. See the console output on how to choose the port and host using command line parameters.

##TODO
* A lot of bug fixing and improvements regarding performance and stability
* Designing a better GUI (see below)
* Better query generation
* Shutdown and restart via GUI
* More stats
* More indexers? Again, see ( https://github.com/theotherp/nzbhydra/issues/20 )
* Auto update (will need help with that one)
* A logo. Nothing too fancy.
* Authentication via form for mobile users
* Include comments, rating, etc or link to them 
* Clean up code base


##To note
As I said query generation is very basic. When selecting a category and doing a search the category will only be used for newznab indexers, for all the raw indexers we will just search using the query. Generating "proper" queries from a category is very hard so you will need to do the filtering visually. Especially with raw indexers that don't support "OR" queries we would need to send a lot of requests to get all the different combinations

Newznab providers don't send information on NFO availablity. If the search results show an NFO link for such an indexer you will need to just try if you can get one.

Not all newznab indexers support search by imdbid, tvdbid and rageid. I added presets for common indexers. If you find an error or know the supported IDs and the indexer's host please let me know. 

Currently the config GUI does not provide any validation apart from the connection tests.

The perfomance could / needs to be improved. Searches can easily take 20 seconds although they're executed in parallel. This is mainly due to the parsing of search results from indexers like NZBIndex being slow, but also due to some problems in the code which I don't really understand so far.

The program is currently in very early alpha. Upgrading to an new version might cause loss of the configuration, stats or history. The console will contain debug information. It will crash. It is definitely not ready for general use.

##Development and how you can help
Generally testing and any bug reports are very welcome.

Any pull requests are also welcome, but I feel I and the program would mostly profit from:
* A web designer / better web design. I'm not going to spend a lot of work to make the frontend look slightly better. 
* Advice regarding stability, error handling, net code (I program Java by day and it shows) and performance (see above)
* More indexers (see above)
* Auto update (see above)
* Any features you know and would expect like restart via GUI, daemonization in linux

### License ###
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

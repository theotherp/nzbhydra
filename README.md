# nzbhydra
NZBHydra is meta search for NZB indexers and the "spiritual successor" to [NZBmegasearcH](https://github.com/pillone/usntssearch). It provides easy access to a number of raw and newznab based indexers.


##Features
* Searches Binsearch, NZBClub, NZBIndex, NZBClub, Womble and all newznab compatible indexers
* Search by IMDB, TVDB and TVRage ID (including season and episode) and filter by age and size
* Rudimentary (for now) query generation, meaning when you search for a movie using e.g. an IMDB ID a query will be generated for raw indexers. Searching for a series season 1 episode 2 will also generate queries for raw indexers, like s01e02 and 1x02
* Grouping of results with the same title and of duplicate results, accounting for result posting time, size, group and poster. By default only one of the duplicates is shown. You can provide an indexer score to influence which one that might be.
* Mostly compatible with newznab search API (tested with Sonarr, CP and NZB 360)
* Included options to add results (single or a bunch) to SABnzbd or NZBGet and show NFOs where available
* Statistics on indexers (average  response time, share of results, access errors), NZB download history  and search history (both via internal GUI and API)
* Reverse proxy compatible without further configuration (tested with Apache)
* A GUI that looks like ass

##How to run
Python 3.4 needed. No plans to backport to any lesser version.

##TODO
* A lot of bug fixing and improvements regarding performance and stability
* Designing a better GUI (see below)
* Better query generation
* Restart via GUI
* More stats
* Selection of downloader category when adding via GUI
* More indexers? I will try to include them if they're not newznab compatible but would need an account
* Auto update (will need help with that one) or at least check of new versions

##To note
As I said query generation is very basic. When selecting a category and doing a search the category will only be used for newznab indexers, for all the raw indexers we will just search using the query. Generating "proper" queries from a category is very hard so you will need to do the filtering visually. Especially with raw indexers that don't support "OR" queries we would need to send a lot of requests to get all the different combinations

Newznab providers don't send information on NFO availablity. If the search results show an NFO link for such an indexer you will need to just try if you can get one.

Currently the config GUI does not provide any validation apart from the connection tests.

The program is currently in very early alpha. Upgrading to an new version might cause loss of the configuration, stats or history.

##Development and how you can help
Generally testing and any bug reports are very welcome.

Any pull requests are also welcome, but I feel I and the program would mostly profit from:
* A web designer. I use Angular 1.4 and would like to keep it because that's what I (barely) know
* Advice regarding stability, error handling, net code (I program Java by day and it shows)
* More indexers (see above)
* Auto update (see above)
* Any features you know and would expect like restart via GUI, daemonization in linux

### License ###
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

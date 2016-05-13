# NZB Hydra changelog

----------
### 0.2.10
Fixed even more: Allow special characters in NZBGet username and password.

Added: Make sure that indexers' and downloaders' names are unique.

Added: Remember state of indexer status box on search results page and remember sorting.

### 0.2.9
Fixed: NZB link should work with URL base.

Fixed: Details link for nZEDb based indexers should link to details pages instead of info pages.

Fixed: Stats and history should display times in proper timezone.

### 0.2.8 
Yeah, well, 0.2.7 changed a lot and broke a lot. Sorry for the problems, I'm trying to get most of them fixed in the coming days.

Fixed: omgwtfnzbs.org results are parsed correctly and will not be skipped.

Fixed: If results are incomplete and not added to the database they're not included in the results either.

Fixed: Config did not like downloader passwords with certain special characters.  

Fixed: Clicking on downloader button would fail.

Changed: Try to prevent "database is locked error" or at least get better logs.

### 0.2.7
Added: Support multiple downloaders.

Added: When the connection test for a downloader or indexer fails you can decide if you want to add it anyway.

Changed: Don't wipe the search field when changing the category. If you already entered something and you select a movie or TV category the autocomplete function is triggered automatically.

Added: Hide disabled indexers in statistics. This only affects the visibility, they're still calculated. If an indexer was never enabled this might skew the statistics, but for now I can't do better.

Fixed: Statistics for downloads and results share were not generated.

People are getting more database locked errors. If you have found a realiable way of reproducing it please let me know. As a test I configured a database timeout. Send me a message if it causes troubles.

### 0.2.6
Fixed: Binsearch downloads would fail after binsearch changed their API.

### 0.2.5
Fixed: Downloading and NFO and details retrieval via API didn't work since 0.2.0. 

Changed: Made sure that the GUID of the returned results is unique ("nzbhydrasearchresult" + internal ID). This may cause some issues with tools that already retrieved results and stored them, but nothing too serious.

### 0.2.4
Fixed: API search results would contain no GUID so sonarr thought they were all the same. This is a quick fix to get things back to running, will improve this later.  

### 0.2.3
Bump version to make sure update is executed. Jump to 0.2.x seems to have caused some troubles.

### 0.2.2
Fixed: Constraint errors handling search results.

### 0.2.1
Fixed: Small problem with last update and empty details links.

### 0.2.0
Changed: Moved minor version to 0.2.0. I would like to say that's because I feel Hydra is more mature now but it's actually because my versioning algorithm thought that 0.0.1a103 < 0.0.1a99...

Changed: From now on hydra will save all found search results to the database for a certain amount of time. This allows easier communication between server and client and some features that I'm planning. This also means that for the first time I need to do a bit
    of data migration. The download history should remain intact, but there's the chance that in some circumstances the migration fails. Sorry...!

### 0.0.1a103
Fixed: Indexers couldn't be deleted in config.

### 0.0.1a101
Fixed: NZBGeek queries contained a superfluous "--".

### 0.0.1a100
Fixed: Bugreport wouldn't work.

### 0.0.1a99
Added: When leaving the config page with unsaved changes ask if the user wants to save, discard or stay on the config page.

Fixed: Some problems with resetting the indexer config.

### 0.0.1a98
Fixed: Layout issues in indexer config. Still not perfect but better.

Fixed: Show API reset time for indexers in UTC and make sure UTC is used.

### 0.0.1a97
Added: Option to always show duplicates in the search results (see Config -> Searching -> Result processing - > Always show duplicates). 

### 0.0.1a96
Added: Show indexer priority (renamed from "Score") in main indexer view. Sort indexers by priority and allow to change it right there.

### 0.0.1a95
Fixed: Newznab indexers were shown twice on search page since last update.

Fixed: ipinfo lib not found in binary release 

### 0.0.1a94
Changed: I redesigned the indexer configuration to look like the one in sonarr. It is a lot less cluttered now. Also connection tests are done automatically and for new indexers the capabilities test is executed automatically. Let me know what you think.

Fixed: Properly recognize empty result pages from binsearch and don't show stack trace if the HTML could not be parsed.

### 0.0.1a93
Added: Support for details and getnfo via API.

Added: Log IP of NZB downloader. Thanks to sanderjo.

### 0.0.1a92
Added: Make errors in config dialog better visible

### 0.0.1a91
Fixed: Bug in max age limit for results.

### 0.0.1a90
Fixed: Color in select list using dark theme.

Added: Ubuntu upstart scripts and better daemon control/logging. Thanks to nikcub.

### 0.0.1a89

Added: Option to set git executable used for updates.

Fixed: Don't try to exclude words with dots, dashes or spaces in queries if the indexer doesn't support it. Indexers that don't follow newznab standards (-- prefix for exclusions) will still not work properly, for now.

Changed: Minor changes in dark theme.

### 0.0.1a88
Added: Dark theme. Feedback appreciated.

### 0.0.1a87
Added: Show NZB downloads per indexer in stats.

Added: HTTP auth for indexers (rarely needed).

Fixed: Re-enable indexer on status page.

### 0.0.1a86
Added: Feature to limit the number of maximum API hits for an indexer in 24 hours.

Added: Show proper page titles.

Added: Show titles for ID based searches in history (if already known).

Fixed: TypeError when using OMGWTF. 

Fixed: Unable to load details page.

### 0.0.1a85
Changed: Try to solve database locked error.

### 0.0.1a84
Added: Add NZB Finder to presets.

Added: Support JSON output for API search results.

Added: Globally define words of which at least one needs to be contained in displayed results.

### 0.0.1a83
Added: Link to TVDB pages from search history for TVRage ID based searches.

Fixed: Error when searching movies with titles containing special characters using the frontend.

### 0.0.1a82
Fixed: Error in search because I wrote code while too tired and checked in without testing. Shame on me.   

### 0.0.1a81
Fixed: Binsearch results where age could not be parsed caused problems, will be ignored.
 
Fixed: Leave settings.cfg untouched if an error occurrs instead of writing an empty file. 

### 0.0.1a80
Fixed: Don't crash whole app if exception in search thread is thrown.
 
Fixed: Make sure that searches are not executed with empty converted search IDs. This would sometimes cause false positives being returned.

### 0.0.1a79
Added: Support for book searches via API. Because a lot of newznab indexers don't support book queries I decided to use query generation instead, 
meaning I do a raw query with the supplied author and/or title in the ebook categories. This might return some/a lot of false positives, but it's 
better than no results at all.
   
Changed: All raw indexers (Binsearch, NZBClub and NZBIndex) are not only enabled for internal searches only. They return too much crap that tools 
using the API will not be able to handle properly as they expect correctly indexed results.  

### 0.0.1a78
Added: Prefix terms in query with "--" to exclude them. Works in addition to global ignored words. 

Fixed: Skip indexers if query generation is enabled, they don't support an ID and the retrieval of the title for the query generation failed.

Fixed: Properly cache retrieved titles for TV or movie IDs.

Fixed: Unable to add user without admin rights.

Fixed: Exclude results violating age or size filters directly in indexer queries where possible and if not then during result processing, not in the GUI.

Fixed: Problems with validation and general usage of authorization config.

Fixed: Don't show update footer for users without admin rights.

### 0.0.1a77
Added: New "Bugreport" tab in the "System" section which gives some advice and provides functions to download anonymized versions of the settings and log which you can post.

Added: Automatically create backup of database and settings before updating. New "Backup" tab in "System" section to create a backup and download existing backup files.

Added: Global setting for maximum age of results.

Added: Errors in the web client will be logged by the server.

Fixed: Properly recognize if wrong schema was supplied for downloader host.

Fixed: If the "Ignore words" settings ended with a comma all search results would be ignored.

Fixed: Use relative base href instead of absolute. Should be compatible with IIS reverse proxy now. No need to preserve the host anymore.

Fixed: Loading of more results would fail.

Fixed: Binsearch results would sometimes have the wrong age.

Changed: Config help texts are now left aligned. 

### 0.0.1a76
Fixed: Binsearch would sometimes return duplicate results.

Changed: Indexer statuses on search results page is minimizable and minimized by default.

Changed: Checkbox to invert selection temporarily disabled because of a bug. Will reenable it when fixed.

### 0.0.1a75
Fixed: Searching TV shows by season/episode via GUI didn't work.

### 0.0.1a74
Fixed: Testing connection of downloader in config didn't work.

### 0.0.1a73
Fixed: Don't provide cert. You need to use your own or better, use a reverse proxy.

### 0.0.1a72
Changed: Threaded server is now activated by default. Improves page loading times and allows parallel searches (yay).

Fixed: Startup would fail without existing settings.cfg.

Fixed: SSL verification failures on Qnap.

### 0.0.1a71
Changed: Reworked caching of assets. Simplifies development process and makes updates a lot smaller.

### 0.0.1a70
Fixed bug where buttons for newznab indexer tests wouldn't work

### 0.0.1a69
Fixed bug where newznab indexers' settings would be incomplete and cause an error when searching.

### 0.0.1a68
Fixed valiidation in config so that the indexer timeout is optional.

### 0.0.1a67
Fixed bug where sending NZBs to downloader wouldn't work.
Removed docker from readme. Will be moved to wiki.
Open NZB details in new tab/window.

### 0.0.1a66
Fixed bug where NFO retrieval didn't work because of a JS error. My bad.

### 0.0.1a65
Fixed bug where searching didn't work because of a JS error. Whoops.

### 0.0.1a64
Rewrote and simplified code for settings which finally allows using an unlimited amount of newznab indexers, along with better GUI handling of those. 
This affected basically every feature in the program, so from experience I'd say I fucked up something which I didn't find during testing, so please let me know ;-) 

Replaced simple users with multi-user system. Add as many users as you want and control if they're allowed to use basic features, see the stats and/or have admin rights. All future searches and downloads will be logged with these users.

Removed caching of search results because it didn't really work and nobody uses it anyway. Therefore removed all cache related settings.

Added validation for most settings in config. It's still possible to make mistakes but... just don't be stupid ;-)

### 0.0.1a63
Fixed bug where searches with empty query parameters would be sent to indexers.

### 0.0.1a62
Improved handling of failed logins.

### 0.0.1a61
Increase timeout for sabNZBd and add logging.

### 0.0.1a60
Fixed bug with newznab search type detection where only a couple of results would be shown in some cases.

Fixed bug where sending links to downloaders would fail with enabled auth.


### 0.0.1a59
Completely rewrote duplicate detection. Fixes an ugly bug, should take 2/3 of the time and easier to fix or expand in the future.
 
Added argument switches for PID file and log file location.
 
When an indexer wasn't searched (e.g. because it doesn't support any of the search types) a message will be shown and the search is not considered unsuccessful.

Use proper caching so that the assets should only be reloaded when they've actually changed (and then actually reload). Should make page loading faster on slow upstream servers and solve problems with outdated assets.

Moved about, updates, log and control sections to their own "System" tab (like sonar ;-)).

Added version history to updates tab.

### 0.0.1a58
Still getting used to writing the change log so I might often forget it for a while.

Fixed a bug where duplicate detection would ironically cause duplicates which caused some weird bugs in the system. Was a pain in the ass to debug and fix.

Added an option to look at this (the changelog) before updating.

Removed "direct" NZB access type. Programs will always need to contact NZB Hydra to get their NZBs.

### 0.0.1a57
First version with changelog

Split settings for base URL and external URL in two. Added option to use local URL for search results.
 
Show notification when update is available.

Prepared for windows release. Expect it in the next week or so.

Spotweb results should now be parsed properly.

### 0.0.1a56
Last version without changelog
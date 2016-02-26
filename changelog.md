# NZB Hydra changelog

----------
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
# NZB Hydra changelog

----------
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
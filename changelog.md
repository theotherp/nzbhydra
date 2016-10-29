# NZB Hydra changelog

----------
### 0.2.162
Changed: Rename omgwtfnzbs.org to omgwtfnzbs and change references in database to keep stats. See [#418](https://github.com/theotherp/nzbhydra/issues/408).

### 0.2.161
Fixed: Max age was not respected in internal movie and TV searches and never used for newznab indexer requests. See [#412](https://github.com/theotherp/nzbhydra/issues/412).

### 0.2.160
Fixed: Error while searching with windows binaries. See [#413](https://github.com/theotherp/nzbhydra/issues/413)

### 0.2.159
Fixed: Windows binaries wouldn't start up because of library inconsistencies. See [#409](https://github.com/theotherp/nzbhydra/issues/409).

### 0.2.158
Changed: Properly use newznab indexer data to check if an NFO is available. See [#329](https://github.com/theotherp/nzbhydra/issues/329).

Fixed: Results from indexers reporting no comments would show comment icon. See [#411](https://github.com/theotherp/nzbhydra/issues/411).
 
Fixed: "Include duplicates" state would not be remembered properly and switching it was wonky. 

Fixed: Expanding duplicates fucked up the layout (since 0.2.154).

### 0.2.157
Fixed: Sorting by grabs works with indexers which don't report the number of grabs. Results from those will be considered as having 0 grabs. See [#407](https://github.com/theotherp/nzbhydra/issues/407).

### 0.2.156
Fixed: Size unavailable for Cardigann results, errors where multiple results with the same GUID were returned by Jackett/Cardigann. See [#410](https://github.com/theotherp/nzbhydra/issues/410).

### 0.2.155
Added: This changelog will now contain links to the associated issues on GitHub. If you have questions or feedback you're welcome to comment there. 

Added: Hydra will try to determine what backend a newznab compatible indexer is running (newznab, nntmux or nzedb) and depending on that use the correct values for NFO retrieval and excluding words. 
Because a search needs to be executed for this analysis it will not be done automatically, so please open the settings for each newznab compatible indexer and click "Check capabilities". Sorry about that.
See [#376](https://github.com/theotherp/nzbhydra/issues/376) and [#329](https://github.com/theotherp/nzbhydra/issues/329).
 
Added: Results in a category for which an indexer is not enabled will be rejected (when searching without specified categories). See [#353](https://github.com/theotherp/nzbhydra/issues/353).

Changed: New omgwtfnzbs host. Existing settings will be migrated. See [#409](https://github.com/theotherp/nzbhydra/issues/408).

Fixed: Sorting by grabs. See [#407](https://github.com/theotherp/nzbhydra/issues/407).

Fixed: Stat times weren't localized. See [#378](https://github.com/theotherp/nzbhydra/issues/378).

### 0.2.154
Added: Torrent search compatible with [Cardigann](https://github.com/cardigann/cardigann/).

Changed: (Hopefully) better algorithm to get details links for NZBs.

Changed: Redesigned results details (again). Removed number of files and comments, replaced text with icons, show comment icon if comments are available. Known issue: No tooltip for fuzzy NFO links.

### 0.2.153
Nothing important.

### 0.2.152
Fixed: Getting debug infos might fail with reverse proxy. 

### 0.2.151
Added: Store Ebook search data in the database. Redesigned search history.

Added: Support for dereferer. Enabled by default. 

Added: Support for HTTP(S) proxy.

### 0.2.150
Changed: Removed some 6box indexers from the presets.

Fixed: Restart after update wouldn't work.

Fixed: Database migration of 0.2.149 would not store new database version meaning the migration might've been done on every startup.

### 0.2.149
Added: Show number of files, grabs and comments where indexers provide this information.

Fixed: Config for removing duplicates for API results was left over.

Fixed: When you enable or disable an indexer in the config, save and go to the search page the indexer's new state is proper represented (i.e. it's not hidden or shown without you having to reload the page).

### 0.2.148
Added: Restore settings from backup via GUI. Please note that this only supports backup ZIPs created with this version or later.

Added: Display number of rejected results in search results view and new button to load all available results.

Added: Enhanced stat calculation:
    * Show the average daily number of API accesses for each indexers
    * Show the average number of unique results each indexer contributed in a search (will only work for searches made from this point on). Also added some text explaining that ;-)
    * Show average number of downloads and searches per day of week and hour of day
    * Added some fancy charts

Changed: Removed option that decided if duplicates should be removed for API calls, this is now always enabled.

Changed: Changed and rewrote database handling. Should (mostly) prevent the notorious "database is locked" errors.

Fixed: Downloads would always be displayed as "API" in the history. 
 
Fixed: NZBIndex result titles would be stripped of all spaces.

Fixed: Indexer statuses box wouldn't remember state.

Fixed: Enabling and disabling indexers would not be properly broadcasted to all areas of the code.

Fixed: Some color inconsistencies.

Fixed: Better handle NZBClub returning an empty page.

Fixed: Better handle parsing errors in general.

### 0.2.147
Changed: Rewrote search result database handling in the hope of fixing this schlamassel.

### 0.2.146
Fixed: Database indexes were never created. This is the reason why saving search results got so slow after some time and, after 0.2.140, search results would be duplicated. 
The migration code needs to delete search results from the database. If you get errors in Sonarr or CP that downloads failed this is the reason. Sorry about that. 

### 0.2.145
Fixed: Login would fail in some cases.

### 0.2.144
Fixed: After last version queries would be cut if pressing return too fast. 

### 0.2.143
Added: Filter results directly on the search results page. Just edit the query or change/add min/max age/size and the already loaded results are filtered on the fly. 

### 0.2.142
Fixed: Remove debug code.

### 0.2.141
Changed: Rewrote some of the search result presentation logic which improves rendering time a bit (still slow, though).

Added/Fixed: Button to invert selection is back and should work as expected.

Added: Shift-click support for the result checkboxes. Click one result, shift click another and all shown displayed checkboses between them will be set to the new value of the first clicked checkbox.
  
Changed: Replaced collapse icons with + and - which I find easier do understand / recognize.

### 0.2.140
Changed: Hopefully improved the performance of writing results to the database. Let me know what happens. 

### 0.2.139
Added: Log how long a search took.

### 0.2.138
Added: Some performance related debug loggings.

### 0.2.137
Added: Button to invert indexer selection on earch page.

Fixed: Indexer statuses box would not store state properly.

### 0.2.136
Fixed: Womble would not search at all.

### 0.2.135
Added: Log a warning if no indexers were picked and provide the reasons.

### 0.2.134
Fixed: Properly follow configuration if required words / regexes should be used for internal or external searches. Added such a switch to the searching config. 

### 0.2.133
Added: Required and forbidden regex support. Separate values for now, so you can either just use comma separated values and / or complex regexes.

### 0.2.132
Added: Option to remove trailing language from newznab results. Some indexers add the language to the result title, preventing proper duplicate detection. Enabled by default.

### 0.2.131
Changed: "Average results shares" statistic now only considers specific searches, so only those where you actually searched for somethic specific, using a query or an ID. This should results in more helpful values.
Note that they're still not precise. When you do a search with only one indexer enable its share will be 100%. If you search with two indexers and the second is offline, then the first one's share is 100% (and the second one's not counted).


### 0.2.130
Fixed: Sonarr search was broken after last update. Sorry...

### 0.2.129
Added: Support for daily shows.

Fixed: Migration from config version 22 didn't work so all users with that version would get errors. Sorry about that.

Changed: Added a small section in the online help to explain indexer priorities.

### 0.2.128
Fixed: Better error handling with testing indexer caps.

### 0.2.127
Fixed: Fallback if indexer was not properly added to the database.

Fixed: Fallback if indexer capabilities settings are not properly set for some reason.

Fixed: Allow empty username and password for sabnzbd.

Changed: Remove "-Obfuscated" from NZBGeek results for better title pairing.

### 0.2.126
Changed: Better error message if an indexer API access could not be saved

### 0.2.125
Changed: Drastically improved processing time. Duplicate detection is about 60% faster. Searches with a lot of new results (not already in the database) are up to 7 times faster (which only shows how bad it was before).

### 0.2.124
Added: Set "no referrer" tag.

Added: API hit limit rolling reset. The indexer doesn't reset the hits at a certain point but you're not allowed to make more than x limits in a 24 hour window. This is used by default.

Changed: Hit limit reset time is defined as hour of day now instead of time of day.

### 0.2.123
Fixed: Categories not set for new indexers not added by selecting a preset.

### 0.2.122
Fixed: When searching TV shows or movies from the GUI using autocomplete don't use the title as query.

### 0.2.121
Added: Include newznab categories in API results where possible.

Fixed: Use proper age threshold for duplicate detection when poster and group are unknown.

Changed: Tweaked (and hopefully improved) duplicate detection. 

### 0.2.120
Added: Include search query in title of search results page.

Fixed: Duplicates were not displayed properly.

### 0.2.119
Fixed: Problem with categories (I hope).

### 0.2.118
Added: Newznab indexers will now be checked for their supported categories and by default only be enabled for those. For those categories that are not standardized by newznab (e.g. Anime, Ebooks, etc.) Hydra will try to determine the used category identifier for each indexer.
 Please note that unfortunately there is no automatic process to do this for indexers that were already added. Please click the "Check types" button for every indexer once and then save. Sorry about that.
  
Added: Anime category and anizb indexer.

Added: When selecting a category on the search page only those indexers that are enabled for that category will be displayed.

Fixed: It looks like I found a solution to the long-standing "database is locked" issue. If true, the fix was embarrassingly, hilariously simple and obvious.

Fixed: Entries in stats and indexer statuses are sorted (either better to worse or by name).

### 0.2.117
Fixed: API key wasn't displayed in omgwtf config.

### 0.2.116
Fixed: Exception when API call with categories and offset > 0 was executed.

### 0.2.115
Added: Basic torrent support. You need to run and configure [Jackett](https://github.com/Jackett/Jackett). Add trackers using the "Jackett" preset in the configuration. They will be only used for internal searches. Torrent clients are not supported and will never be.
You can search manually and download the torrent files. That should be enough for most.

Added: Limit indexers to certain categories. Makes most sense when you have added specialized torrent trackers and don't want to use them for categories in which they don't have content anyway. 

Changed: Required and forbidden words are now handled a bit differently. If a word contains a dot or a dash (".", "-") then the word will be searched for anywhere in a result title. If it does not contain a dot or a dash then
all the words in the title will be compared with the word. Example: Forbidding "abc" will dismiss the result "abc.def" or "abc def" but allow "abcdef" or "ab-cdef". Forbidding "ab-c" will dismis "ab-cdef".
This way you'll be able, for example, to require release groups like "EA" without allowing a result like "Peachy-BOSS" and on the other hand forbidding "WEB-DL" without letting through "Spider.web-Dl.ist".
I think this is the approach that will handle the most common cases.

### 0.2.114
Changed: Required words are now searched on a word basis instead of full-text, meaning that at least one of the required words needs to be a word in a result's title, not just be present anywhere in the title.
 
Fixed: "All" category wasn't available in selection box after having selected another category.

### 0.2.113
Added: SOCKS proxy support by sanderjo

### 0.2.112
Fixed: Return correct NZBGeek details links.

### 0.2.111
Fixed: Lxml wouldn't load even if installed properly.

Fixed: Download of debug infos wouldn't work in firefox.

### 0.2.110
Fixed: Make sure iconCssClass is set.

### 0.2.109
Fixed: Category mapping wouldn't work with omgwtf.

Fixed: URL base was not included in NZB links when external URL was not set. Now the local IP address, configured port and scheme are used. Tools on your computer (and inside your network) should be able to use the generated links.
  If you need to send links to tools outside your network you have to set the external URL.
  
Fixed: Excluding words with "--" in the search field didn't work.

Fixed: Total number of results was not put into API search result if offset was 0.


### 0.2.108
Changed: Rewrote auth handling. Unfortunately form based auth only works when calls from the GUI are done, as soon as you call any function from outside (e.g. CP) the token header is
 missing and you will be asked for credentials using basic auth. Now, when you enter them, hydra will accept them even with form based auth enabled.
  I might change that behavior in the future but for now it stands.

### 0.2.107
Fixed: Repeating search from history wouldn't work (in multiple ways).

Fixed: ID based search from the GUI didn't work.

### 0.2.106
Fixed: Forbidden and ignored words not displayed in config.

Fixed: Download of bugreport would not work with auth type "Form".

Fixed: Error with API search and categories due to stupid mistake but caused by fucking Python 2.7.

### 0.2.105
Fixed: Set appropriate categories when API searches are done ("Movies" for movie search, etc.) 

### 0.2.104
Fixed: Stats and config invisible with no auth enabled.

### 0.2.103
Added: Several changes in the handling and configuration of categories.

* New category section in the config. Define required and forbidden words for every category and if they should be applied for external and/or internal searches.  This allows you to finetune results for CP or Sonarr, for example.

* Define newznab categories for every Hydra category. These categories will be used when you search with that category from the GUI. That way you can control if foreign movies should be included in movie searches, for example.

* Decide for every category if you want to ignore results from it for external and/or internal searches.

Added: Online help in the configuration.

Added: Improved test coverage and started to write more integration tests. Should somewhat decrease chance of breaking bugs, at least for API. I still don't have frontend tests.

Changed: Login and logout functionality. The navigation only shows links to sections the current user is allowed to visit. Click the login button in the upper right to login. Click it again to logout.
If you use basic auth and logged out make sure to close the browser so that the auth header is removed.
 
Changed: Don't require auth for NZB details links when form based auth is enabled. Should prevent troubles with viewing details from external tools like CP and the security risks are negligible. 

Fixed: Don't display an NZB download as failed if it was only redirected (then we don't know if it was successful).

Fixed: Error where indexers tab in config could not be opened.

Fixed: When migration of old config fails keep the config instead of overwriting it. Provide feedback and stop program.

Fixed: Support for custom downloader icons was broken.

### 0.2.102
Changed: Using ! to exclude words when querying newznab indexers. This should be compatible with more indexers and provide the wanted results. Thanks to judhat2 for the research and tests.

Fixed: Fallback to pubdate when usenet date cannot be parsed.

### 0.2.101
Added: Return category in API search results.

Fixed: If log file name is provided in command line show that in GUI instead of the configured one.

### 0.2.100
Added: Show log in scrollable area.

Added: Comic category. Searches in newznab comic category if available, otherwise in general ebook category or just for the query in case of raw search engines.

Added: Link to indexer details page for entries in download history.

Fixed: Selecting search results from duplicates / same name rows wouldn't work.

Fixed: Search would ask for auth even if access wasn't restricted.

### 0.2.99
Fixed: Downloader default category wouldn't be used.

### 0.2.98
Changed: Provide a bit better info when auth fails.

Changed: Provide better feedback when the connection test to an indexer fails.

Fixed: Form based auth wouldn't work with subdirectories on reverse proxies.

### 0.2.97
Fixed: Indexer status box state wasn't remembered.

Fixed: Changelog would either show too much or not enough...

### 0.2.96
Fixed: Search box would disappear when showing search results.

Fixed: Sensitive downloader data would be sent to non-admins. Sorry. 

Fixed: Changelog would be shown empty.

### 0.2.95
Added: Decide if you want to authenticate using HTTP basic auth or a login form. If you have users configured please make sure that everything is in order.

Added: SimplyNZBs added to the presets.

Fixed: Displayed times in stats were all sorts of wrong.  

### 0.2.94
Probably not fixed but less likely: Database is locked.
 
Fixed: Details link would point to "http://api.indexer.com/details/..." and not work.
 
Fixed: When adding multiple indexers one after the other the data from the old indexer would be still there.

Added: Option if IP addresses should be logged. Failed logins will still be logged with the used IP address.   

### 0.2.93

Fixed: /details links wouldn't work.

### 0.2.92

Fixed: Bug report info generating should work again.

### 0.2.91
Fixed even more: Allow special characters in NZBGet username and password.

Changed: Jumped to version 0.2.91 because I'm an idiot and the version check did a string comparison, so 0.2.91 was the next minor version that would be found as an update. Also fixed some bugs in the changelog retrieval. 

Added: Make sure that indexers' and downloaders' names are unique.

Added: Remember state of indexer status box on search results page and remember sorting.

Added: Popover name of downloader and allow to select an icon from http://fontawesome.io/icons/ instead of the default icon.

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
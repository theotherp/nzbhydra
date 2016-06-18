## Hosting
If you use Hydra behind a reverse proxy you might need to set the URL base to a value like "/nzbhydra". 

If you accesses Hydra with tools running outside your network (for example from your phone) set the external URL so that it matches the full Hydra URL. That way the NZB links returned in the search results refer to your global URL and not your local address.

You can use SSL but I recommend using a reverse proxy with SSL. See [the wiki](https://github.com/theotherp/nzbhydra/wiki/Reverse-proxies-and-URLs).

## Security
Erase the API key to disable authentication by API key. Some tools might not even support that, so better leave it there, even if you use Hydra only locally.
 
## Logging
The base settings should suffice for most users. If you want you can enable logging of IP adresses for failed logins and NZB downloads.

## Updating
You can set your git executable if it's not in your path and not found by Hydra.

I strongly recommend to stay on master. I regularly fuck up stuff on the other branches (more so than on master).

## Other
By default all found results are stored in the database for 7 days until they're deleted. After that any links to Hydra results still stored elsewhere become invalid. You can increase the limit if you want, the disc space needed is negligible (about 75 MB for 7 days on my server)*[]: 

Do **not** enable debugging until you know what you're doing.

Running the threaded server allows for parallel access to hydra so multiple tools can search at the same time. I've never had problems with it but some users reliably experience database locking issues. You might do some tests.
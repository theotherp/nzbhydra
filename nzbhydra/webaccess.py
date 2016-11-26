import os

import requests
from furl import furl


proxies = None

os.environ['no_proxy'] = '127.0.0.1,localhost'


def set_proxies(http, https=None):
    global proxies
    if http is None:
        return
    try:
        from nzbhydra.log import logger
        cleanHttp = getCleanProxyUrl(http)
        cleanHttps = getCleanProxyUrl(https if https is not None else http)
        logger.info("Using proxy settings: http=%s, https=%s (username and password not shown)" % (cleanHttp, cleanHttps))
        logger.info("Proxy will be disabled for accesses to localhost and 192.168.*.* addresses")
        proxies = {"http": http, "https": https if https is not None else http}
    except:
        logger.error("Unable to set SOCKS proxy. Make sure it follows the format socks5://user:pass@host:port")


def getCleanProxyUrl(url):
    f = furl(url)
    return "%s://%s:%d" % (f.scheme, f.host, f.port)


def get(url, **kwargs):
    global proxies
    myproxies = proxies if proxies is not None and furl(url).host not in ["127.0.0.1", "localhost"] and "192.168" not in str(url) else None
    return requests.get(url, proxies=myproxies, verify=False, **kwargs)


def post(url, **kwargs):
    global proxies
    myproxies = proxies if proxies is not None and furl(url).host not in ["127.0.0.1", "localhost"] and "192.168" not in str(url) else None
    return requests.post(url, proxies=myproxies, verify=False, **kwargs)

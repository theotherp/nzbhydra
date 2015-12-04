import re
import urllib


RE_QUOTE = re.compile('^[-A-Za-z0-9~!*()_.\',:@$/]*$')


def quote(x):
    if RE_QUOTE.match(x):
        return x

    return urllib.quote(x.encode('utf-8'))\
        .replace('%2C', ',', 'g')\
        .replace('%3A', ':', 'g')\
        .replace('%40', '@', 'g')\
        .replace('%24', '$', 'g')\
        .replace('%2F', '/', 'g')\
        .replace('%20', '+', 'g')

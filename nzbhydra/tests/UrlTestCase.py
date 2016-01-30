import unittest


import string
import re
import struct
import socket

from urlparse import urlsplit
from urlparse import parse_qsl
from urllib import urlencode
from urllib import quote
from urllib import unquote
from posixpath import normpath

"""
inspired a lot from 
http://google-safe-browsing.googlecode.com/svn/trunk/python/expression.py
and
https://github.com/rbaier/urltools
"""

SAFE_CHARS = ''.join([c for c in (string.digits + string.ascii_letters + string.punctuation) if c not in '%#'])
VALID_DOMAIN = re.compile('^[a-zA-Z\d-]{1,63}(\.[a-zA-Z\d-]{1,63})*$')


def escape(unescaped_str):
    unquoted = unquote(unescaped_str)
    while unquoted != unescaped_str:
        unescaped_str = unquoted
        unquoted = unquote(unquoted)

    return quote(unquoted, SAFE_CHARS)


def url_normalize(url):
    url = str(url).replace('\t', '').replace('\r', '').replace('\n', '')
    url = url.strip()
    testurl = urlsplit(url)
    if testurl.scheme == '':
        url = urlsplit('http://' + url)
    elif testurl.scheme in ['http', 'https']:
        url = testurl
    else:
        return None

    scheme = url.scheme

    if url.netloc:
        try:
            hostname = url.hostname.rstrip(':')

            port = None
            try:
                port = url.port
            except ValueError:
                pass

            username = url.username
            password = url.password

            hostname = [part for part in hostname.split('.') if part]

            # convert long ipv4
            # here will fail domains like localhost
            if len(hostname) < 2:
                hostname = [socket.inet_ntoa(struct.pack('!L', long(hostname[0])))]

            hostname = '.'.join(hostname)
            hostname = hostname.decode('utf-8').encode('idna').lower()

            if not VALID_DOMAIN.match(hostname):
                return None

        except Exception as e:
            return None

        netloc = hostname
        if username:
            netloc = '@' + netloc
            if password:
                netloc = ':' + password + netloc
            netloc = username + netloc

        if port:
            if scheme == 'http':
                port = '' if port == 80 else port
            elif scheme == 'https':
                port = '' if port == 443 else port

            if port:
                netloc += ':' + str(port)

        path = netloc + normpath('/' + url.path + '/').replace('//', '/')
    else:
        return None

    query = parse_qsl(url.query, True)
    query.sort()
    query = urlencode(query)

    fragment = url.fragment

    return (('%s://%s?%s#%s' % (scheme, escape(path), query, escape(fragment))).rstrip('?#/ '))


class UrlTestCase(unittest.TestCase):

    
    def assertUrlEqual(self, url1, url2):
        self.assertEqual(url_normalize(url1), url_normalize(url2))

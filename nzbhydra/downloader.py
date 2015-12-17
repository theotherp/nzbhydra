from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from builtins import *
from builtins import str
from future import standard_library

from nzbhydra.exceptions import DownloaderException

standard_library.install_aliases()
import base64
import json
import logging
import socket
import xmlrpc.client
from furl import furl
import requests
from requests.exceptions import HTTPError, SSLError, ConnectionError
from nzbhydra.config import sabnzbdSettings, nzbgetSettings


class Downloader(object):
    def test(self, host, ssl=False, port=None, username=None, password=None, apikey=None):
        return True

    def add_link(self, link, title, category):
        return True

    def add_nzb(self, content, title, category):
        return True

    def get_categories(self):
        return []


class Nzbget(Downloader):
    logger = logging.getLogger('root')

    def get_rpc(self, host=None, ssl=None, port=None, username=None, password=None):
        if host is None:
            host = nzbgetSettings.host.get()
        if ssl is None:
            ssl = nzbgetSettings.ssl.get()
        if port is None:
            port = nzbgetSettings.port.get()
        if username is None:
            username = nzbgetSettings.username.get()
        if password is None:
            password = nzbgetSettings.password.get()
        f = furl()
        f.host = host
        f.username = username
        f.password = password
        f.scheme = "https" if ssl else "http"
        f.port = port
        f.path.add("xmlrpc")

        return xmlrpc.client.ServerProxy(f.tostr())

    def test(self, host, ssl=False, port=None, username=None, password=None, apikey=None):
        rpc = self.get_rpc(host, ssl, port, username, password)

        try:
            if rpc.writelog('INFO', 'NZB Hydra connected to test connection'):
                version = rpc.version()
                #todo: show error if version older than 13
                if int(version[:2]) < 13:
                    return False, "NZBGet needs to be version 13 or higher"
                self.logger.debug('Successfully connected to NZBGet')
            else:
                self.logger.info('Successfully connected to NZBGet, but unable to send a message')
        except socket.error:
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            return False, "NZBGet is not responding under this address, scheme and port"
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
                return False, "Wrong credentials"
            else:
                self.logger.error('Protocol error: %s', e)
            return False, str(e)

        return True, ""

    def add_link(self, link, title, category):
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # NZBGet skips entries of which the filename does not end with NZB
                title += ".nzb"
        category = "" if category is None else category

        rpc = self.get_rpc()
        try:
            rcode = rpc.append(title, link, category, 0, False, False, "", 0, "SCORE",[])
            if rcode > 0:
                self.logger.info("Successfully added %s from %s to NZBGet" % (title, link))
                return True
            else:
                self.logger.error("NZBGet returned an error while adding %s from %s" % (title, link))
                return False
        except socket.error:
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            return False
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
            else:
                self.logger.error('Protocol error: %s', e)
            return False

    def add_nzb(self, content, title, category):
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # NZBGet skips entries of which the filename does not end with NZB
                title += ".nzb"
        category = "" if category is None else category

        encoded_content = base64.standard_b64encode(content).decode()  # Took me ages until I found out I was still sending bytes instead of a string 

        rpc = self.get_rpc()
        try:
            rcode = rpc.append(title, encoded_content, category, 0, False, False, "", 0, "SCORE")
            if rcode > 0:
                self.logger.info("Successfully added %s to NZBGet" % title)
                return True
            else:
                self.logger.error("NZBGet returned an error while adding NZB for %s" % title)
                return False
        except socket.error as e:
            self.logger.debug(str(e))
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            return False
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
            else:
                self.logger.error('Protocol error: %s', e)
            return False
        
    def get_categories(self):
        try:
            rpc = self.get_rpc()
            config = rpc.config()
            categories = []
            for i in config:
                if "Category" in i["Name"] and "Name" in i["Name"]:
                    categories.append(i["Value"])
            return categories

        except socket.error as e:
            self.logger.debug(str(e))
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            raise DownloaderException("Unable to contact NZBGet")
        
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
            else:
                self.logger.error('Protocol error: %s', e)
            raise DownloaderException("Unable to contact NZBGet")


class Sabnzbd(Downloader):
    logger = logging.getLogger('root')

    def get_sab(self, host=None, port=None, scheme=None, apikey=None, username=None, password=None):
        if host is None:
            host = sabnzbdSettings.host.get()
        if port is None:
            port = sabnzbdSettings.port.get()
        if apikey is None:
            apikey = sabnzbdSettings.apikey.get()
        if username is None:
            username = sabnzbdSettings.username.get()
        if password is None:
            password = sabnzbdSettings.password.get()
        f = furl()
        if apikey:
            f.add({"apikey": apikey})
        elif username and password:
            pass
        else:
            raise DownloaderException("Neither API key nor username/password provided")
        f.scheme = "https" if scheme else "http"
        f.host = host
        f.port = port
        f.path.add("api")
        f.add({"output": "json"})

        return f

    def test(self, host, ssl=False, port=None, username=None, password=None, apikey=None):
        f = self.get_sab(host, port, ssl, apikey, username, password)
        f.add({"mode": "qstatus"})
        try:
            r = requests.get(f.tostr(), verify=False)
            r.raise_for_status()
            if "state" in json.loads(r.text).keys():
                return True, ""
            else:
                return False, "Credentials wrong?"

        except (SSLError, HTTPError, ConnectionError) as e:
            self.logger.exception("Error while trying to connect to sabnzbd")
            return False, "SABnzbd is not responding under this address, scheme and port"

    def add_link(self, link, title, category):
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # sabnzbd skips entries of which the filename does not end with NZB
                title += ".nzb"

        f = self.get_sab()
        f.add({"mode": "addurl", "name": link, "nzbname": title})
        if category is not None:
            f.add({"cat": category})
        try:
            r = requests.get(f.tostr(), verify=False)
            r.raise_for_status()
            return r.json()["status"]
        except (SSLError, HTTPError, ConnectionError):
            self.logger.exception("Error while trying to connect to sabnzbd")
            return False

    def add_nzb(self, content, title, category):
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # sabnzbd skips entries of which the filename does not end with NZB
                title += ".nzb"

        f = self.get_sab()
        f.add({"mode": "addfile", "nzbname": title})
        if category is not None:
            f.add({"cat": category})
        try:
            files = {'nzbfile': (title, content)}
            r = requests.post(f.tostr(), files=files, verify=False)
            r.raise_for_status()
            return r.json()["status"]
        except (SSLError, HTTPError, ConnectionError):
            self.logger.exception("Error while trying to connect to sabnzbd")
            return False

    def get_categories(self):
        f = self.get_sab()
        f.add({"mode": "get_cats", "output": "json"})
        try:
            r = requests.get(f.tostr(), verify=False)
            r.raise_for_status()
            return r.json()["categories"]
        except (SSLError, HTTPError, ConnectionError):
            self.logger.exception("Error while trying to connect to sabnzbd")
            raise DownloaderException("Unable to contact SabNZBd")

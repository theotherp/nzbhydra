from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import urllib

from builtins import *
from builtins import str
from future import standard_library

from nzbhydra import webaccess
from nzbhydra.exceptions import DownloaderException, DownloaderNotFoundException

#standard_library.install_aliases()
import base64
import json
import logging
import socket
import xmlrpc.client
from furl import furl
import requests
from requests.exceptions import HTTPError, SSLError, ConnectionError, ReadTimeout, InvalidSchema, MissingSchema
from nzbhydra import config


class Downloader(object):
    
    def add_link(self, link, title, category):
        return True

    def add_nzb(self, content, title, category):
        return True

    def get_categories(self):
        return []


class Nzbget(Downloader):
    logger = logging.getLogger('root')
    
    def __init__(self, setting):
        self.setting = setting

    def get_rpc(self, host=None, ssl=None, port=None, username=None, password=None):
        if host is None:
            host = self.setting.host
        if ssl is None:
            ssl = self.setting.ssl
        if port is None:
            port = self.setting.port
        if username is None:
            username = self.setting.username
        if password is None:
            password = self.setting.password
        f = furl()
        f.host = host
        f.scheme = "https" if ssl else "http"
        f.port = port
        if username is not None and password is not None:
            f.path.add("%s:%s" % (username, password))
        f.path.add("xmlrpc")

        return xmlrpc.client.ServerProxy(f.tostr())

    def test(self, setting):
        self.logger.debug("Testing connection to snzbget")
        rpc = self.get_rpc(setting.host, setting.ssl, setting.port, setting.username, urllib.quote(setting.password.encode("utf-8")))

        try:
            if rpc.writelog('INFO', 'NZB Hydra connected to test connection'):
                version = rpc.version()
                #todo: show error if version older than 13
                if int(version[:2]) < 13:
                    self.logger.error("NZBGet needs to be version 13 or higher")
                    return False, "NZBGet needs to be version 13 or higher"
                self.logger.info('Connection test to NZBGet successful')
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
        except Exception as e:
            self.logger.exception("Unknown error while communicating with NZBGet")
            return False, str(e)
        return True, ""

    def add_link(self, link, title, category):
        self.logger.debug("Sending add-link request for %s to nzbget" % title)
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
        self.logger.debug("Sending add-nzb request for %s to nzbget" % title)
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
        self.logger.debug("Sending categories request to nzbget")
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

    def __init__(self, setting):
        self.setting = setting
    

    def get_sab(self, url=None, apikey=None, username=None, password=None):
        if url is None:
            url = self.setting.url
        if apikey is None:
            apikey = self.setting.apikey
        if username is None:
            username = self.setting.username
        if password is None:
            password = self.setting.password
        f = furl(url)
        f.path.add("api")
        if apikey:
            f.add({"apikey": apikey})
        elif username and password:
            pass
        else:
            raise DownloaderException("Neither API key nor username/password provided")
        f.add({"output": "json"})

        return f

    def test(self, setting):
        self.logger.debug("Testing connection to sabnzbd")
        try:
            f = self.get_sab(setting.url, setting.apikey, setting.username, setting.password)
            f.add({"mode": "qstatus"})
            r = webaccess.get(f.tostr(), timeout=15)
            r.raise_for_status()
            if "state" in json.loads(r.text).keys():
                self.logger.info('Connection test to sabnzbd successful')
                return True, ""
            else:
                self.logger.info("Access to sabnzbd failed, probably due to wrong credentials")
                return False, "Credentials wrong?"
        except DownloaderException as e:
            self.logger.error("Error while trying to connect to sabnzbd: %s" % e)
            return False, str(e)
        except (SSLError, HTTPError, ConnectionError, ReadTimeout, InvalidSchema, MissingSchema) as e:
            self.logger.error("Error while trying to connect to sabnzbd: %s" % e)
            return False, "SABnzbd is not responding"

    def add_link(self, link, title, category):
        self.logger.debug("Sending add-link request for %s to sabnzbd" % title)
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
            r = webaccess.get(f.tostr(), timeout=15)
            r.raise_for_status()
            return r.json()["status"]
        except (SSLError, HTTPError, ConnectionError, ReadTimeout, InvalidSchema, MissingSchema):
            self.logger.exception("Error while trying to connect to sabnzbd using link %s" % link)
            return False

    def add_nzb(self, content, title, category):
        self.logger.debug("Sending add-nzb request for %s to sabnzbd" % title)
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
            r = webaccess.post(f.tostr(), files=files, timeout=15)
            r.raise_for_status()
            return r.json()["status"]
        except (SSLError, HTTPError, ConnectionError, ReadTimeout):
            self.logger.exception("Error while trying to connect to sabnzbd with URL %s" % f.url)
            return False

    def get_categories(self):
        self.logger.debug("Sending categories request to sabnzbd")
        f = self.get_sab()
        f.add({"mode": "get_cats", "output": "json"})
        try:
            r = webaccess.get(f.tostr(), timeout=15)
            r.raise_for_status()
            return r.json()["categories"]
        except (SSLError, HTTPError, ConnectionError, ReadTimeout, InvalidSchema, MissingSchema):
            self.logger.exception("Error while trying to connect to sabnzbd with URL %s" % f.url)
            raise DownloaderException("Unable to contact SabNZBd")


def getDownloaderInstanceByName(name):
    for i in config.settings.downloaders:
        if i.name == name:
            return getInstanceBySetting(i)
    raise DownloaderNotFoundException("No downloader with name %s found" % name)


def getInstanceBySetting(setting):
    if setting.type == "sabnzbd":
        return Sabnzbd(setting)
    if setting.type == "nzbget":
        return Nzbget(setting)
    raise DownloaderNotFoundException("No downloader with type %s found" % setting.type)
        
    
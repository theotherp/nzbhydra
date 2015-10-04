import base64
import logging
import socket
import xmlrpc.client

from furl import furl
import requests
from requests.packages.urllib3.exceptions import RequestError


class Downloader(object):
    def test(self) -> bool:
        return True

    def add_link(self, link: str, title: str, category: str) -> bool:
        return True

    def add_nzb(self, content: str, title: str, category: str) -> bool:
        return True


class Nzbget(Downloader):
    logger = logging.getLogger('root')

    def get_rpc(self):
        host = "127.0.0.1"
        ssl = False
        port = 6789
        username = "nzbget"
        password = "tegbzn6789"
        f = furl(host)
        f.username = username
        f.password = password
        f.scheme = "https" if ssl else "http"
        f.port = port
        f.path = "xmlrpc"

        return xmlrpc.client.ServerProxy(f.tostr())

    def test(self) -> bool:
        rpc = self.get_rpc()

        try:
            if rpc.writelog('INFO', 'NZB Hydra connected to test connection'):
                # version = rpc.version()
                # todo: show error if version older than 13
                self.logger.debug('Successfully connected to NZBGet')
            else:
                self.logger.info('Successfully connected to NZBGet, but unable to send a message')
        except socket.error:
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            return False
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
            else:
                self.logger.error('Protocol error: %s', e)
            return False

        return True

    def add_link(self, link: str, title: str, category: str) -> bool:
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # NZBGet skips entries of which the filename does not end with NZB
                title += ".nzb"
        category = "" if category is None else category

        rpc = self.get_rpc()
        try:
            rcode = rpc.append(title, link, category, 0, False, False, "", 0, "SCORE")
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

    def add_nzb(self, content: str, title: str, category: str) -> bool:
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
        except socket.error:
            self.logger.error('NZBGet is not responding. Please ensure that NZBGet is running and host setting is correct.')
            return False
        except xmlrpc.client.ProtocolError as e:
            if e.errcode == 401:
                self.logger.error('Wrong credentials')
            else:
                self.logger.error('Protocol error: %s', e)
            return False


class Sabnzbd(Downloader):
    logger = logging.getLogger('root')

    def get_sab(self):
        host = "127.0.0.1"
        ssl = False
        port = 8086
        username = None
        password = None
        apikey = "d471a402a71542bdd255667df2dd45cc"
        f = furl()
        if username is not None:
            f.username = username
        if password is not None:
            f.password = password
        if apikey is not None:
            f.add({"apikey": apikey})
        f.scheme = "https" if ssl else "http"
        f.host = host
        f.port = port
        f.path.add("api")
        f.add({"output": "json"})

        return f

    def test(self) -> bool:
        f = self.get_sab()
        f.add({"mode": "version"})
        try:
            r = requests.get(f.tostr())
            r.raise_for_status()
            return True
        except RequestError:
            self.logger.error("Error while trying to connect to sabnzbd")
            return False

    def add_link(self, link: str, title: str, category: str) -> bool:
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # NZBGet skips entries of which the filename does not end with NZB
                title += ".nzb"

        f = self.get_sab()
        f.add({"mode": "addurl", "name": link, "nzbname": title})
        if category is not None:
            f.add({"cat": category})
        try:
            r = requests.get(f.tostr())
            r.raise_for_status()
            return r.json()["status"]
        except RequestError:
            self.logger.error("Error while trying to connect to sabnzbd")
            return False

    def add_nzb(self, content: str, title: str, category: str) -> bool:
        if title is None:
            title = ""
        else:
            if not title.endswith(".nzb"):  # NZBGet skips entries of which the filename does not end with NZB
                title += ".nzb"

        f = self.get_sab()
        f.add({"mode": "addfile", "nzbname": title})
        if category is not None:
            f.add({"cat": category})
        try:
            files = {'nzbfile': (title, content)}
            r = requests.post(f.tostr(), files=files)
            r.raise_for_status()
            return r.json()["status"]
        except RequestError:
            self.logger.error("Error while trying to connect to sabnzbd")
            return False

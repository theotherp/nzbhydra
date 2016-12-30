import json
import os
import requests
from bs4 import BeautifulSoup
from subprocess import call
from nzbhydra import update

DO_PUSH = True
DO_RELEASE = True

_, version = update.get_current_version()

html = update.getVersionHistory(sinceLastVersion=True)
find_all = [x.text for x in BeautifulSoup(html, "lxml").findAll("p")]
text = '\n\n'.join(find_all)

returncode = call(["buildWindowsdist.cmd", version])

if returncode == 0 and DO_PUSH:
    returncode = call(["pushWindowsdist.cmd", version])

if returncode == 0 and DO_RELEASE:
    token = os.environ.get("TOKEN")
    data = {"tag_name": version, "target_commitish": "master", "name": version, "body": text, "draft": False, "prerelease": False}
    r = requests.post("https://api.github.com/repos/theotherp/nzbhydra-windows-releases/releases?access_token=" + token, data=json.dumps(data))
    r.raise_for_status()

    token = os.environ.get("TOKEN")
    data = {"tag_name": version, "target_commitish": "master", "name": version, "body": text, "draft": False, "prerelease": False}
    r = requests.post("https://api.github.com/repos/theotherp/nzbhydra/releases?access_token=" + token, data=json.dumps(data))
    r.raise_for_status()

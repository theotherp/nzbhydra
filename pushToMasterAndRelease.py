import json
import os

import requests
from bs4 import BeautifulSoup

from nzbhydra import update

from subprocess import call

returncode = call(["git.exe", "push", "origin", "master"])

if returncode == 0:
    _, version = update.get_current_version()

    html = update.getVersionHistory(sinceLastVersion=True)
    find_all = [x.text for x in BeautifulSoup(html, "lxml").findAll("p")]
    text = '\n\n'.join(find_all)

    token = os.environ.get("TOKEN")
    data = {"tag_name": version, "target_commitish": "master", "name": version, "body": text, "draft": False, "prerelease": False}
    r = requests.post("https://api.github.com/repos/theotherp/nzbhydra/releases?access_token=" + token, data=json.dumps(data))
    r.raise_for_status()


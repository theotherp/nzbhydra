import json
import os
from subprocess import call
from bs4 import BeautifulSoup
import requests
from nzbhydra import update

_, version = update.get_current_version()

html = update.getVersionHistory(sinceLastVersion=True)
find_all = [x.text for x in BeautifulSoup(html, "lxml").findAll("p")]
text = '\n\n'.join(find_all)

returncode = call(["buildWindowsdist.cmd", version])

# if returncode == 0:
#     token = os.environ.get("TOKEN")
#     data = {"tag_name": version, "target_commitish": "master", "name": version, "body": text, "draft": False, "prerelease": False}
#     r = requests.post("https://api.github.com/repos/theotherp/nzbhydra-windows-releases/releases?access_token=" + token, data=json.dumps(data))
#     r.raise_for_status()
import json
import os

import requests
import subprocess
from bs4 import BeautifulSoup

from nzbhydra import update

p = subprocess.Popen("git.exe push origin master", stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
output, err = p.communicate()
returncode = p.returncode
if output:
    output = output.strip()
print("git output: " + output)

if returncode == 0:
    _, version = update.get_current_version()

    html = update.getVersionHistory(sinceLastVersion=True)
    find_all = [x.text for x in BeautifulSoup(html, "lxml").findAll("p")]
    text = '\n\n'.join(find_all)

    token = os.environ.get("TOKEN")
    data = {"tag_name": version, "target_commitish": "master", "name": version, "body": text, "draft": False, "prerelease": False}
    r = requests.post("https://api.github.com/repos/theotherp/nzbhydra/releases?access_token=" + token, data=json.dumps(data))
    r.raise_for_status()


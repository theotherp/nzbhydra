import os
from distutils.core import setup

import py2exe

# dummy use so pycharm doesn't remove it as unused import
_ = py2exe

data_files = []


def findDataFiles(folder):
    files = []
    for root, dirnames, filenames in os.walk(os.path.join("nzbhydra", folder)):
        for filename in filenames:
            filename = os.path.join(root, filename)
            files.append((root.replace("nzbhydra\\", ""), [filename]))
    return files


for folder in ["static", "templates", "data"]:
    data_files.extend(findDataFiles(folder))
data_files.append((".", ["version.txt", "README.md", "LICENSE"]))

setup(
        console=['nzbhydra.py'],
        data_files=data_files,
        options={
            "py2exe": {
                "includes": ["flask_cache", "flask_session"],
                "skip_archive": False,
                "dist_dir": "distpy2exe"
            }
        })

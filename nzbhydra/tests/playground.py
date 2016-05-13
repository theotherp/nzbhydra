from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import random
import string


def versiontuple(v):
    filled = []
    for point in v.split("."):
        filled.append(point.zfill(8))
    return tuple(filled)

print(versiontuple("0.2.10") > versiontuple("0.2.9"))
print("0.2.91" > "0.2.9")
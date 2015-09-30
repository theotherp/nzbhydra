import os
import re
import unittest
from furl import furl
import requests

import responses

from nzbhydra import run


#todo. doesn't work because the actual request in handleRequest is also caught by the mock. Found no way to prevent that

# def handleRequest(request):
#     url = request.url
#     host = furl(url.split("?")[0]).host
#     args = []
#     filename = hash(host)
#     for i in url.split("?")[1].split("&"):
#         kv = i.split("=")
#         args.append((kv[0], kv[1]))
#     args = sorted(args, key=lambda x: x[0])
#     for kv in args:
#         filename = "%s--%s-%s" % (filename, kv[0], kv[1])
#     filename = "tests\\cache\\" + filename + ".cache"
#     if not os.path.exists(filename):
#         r = requests.get(url)
#         if r.status_code == 200:
#             with open(filename, "w") as f:
#                 f.write(r.content)
#         else:
#             print("Status code" + str(r.status_code))
#     with open(filename, "r") as f:
#         body = f.read()
#         return 200, {}, body
#             
#     print(filename)
# 
# with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
#     rsps.add_callback(responses.GET, re.compile(r".*(\\.com)|(\\.cr)|(\\.org)\\/.*"), callback=handleRequest)
#     run()

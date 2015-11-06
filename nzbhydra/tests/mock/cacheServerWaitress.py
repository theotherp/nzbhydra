from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
from future import standard_library
standard_library.install_aliases()
from builtins import *
from waitress import serve

from nzbhydra.tests.mock.cacheServer import app as application

serve(application, port=5001, host="127.0.0.1")

import sys

from tests.mock.mockServer import app as application
from waitress import serve

serve(application, port=5001, host="0.0.0.0")
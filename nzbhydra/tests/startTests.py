from os.path import dirname, join, abspath
from sys import path
import pytest

base_path = dirname(dirname(dirname(abspath(__file__))))
path.insert(0, join(base_path, 'nzbhydra'))
path.insert(0, join(base_path, 'libs'))
print(path)
pytest.main("--capture=sys")
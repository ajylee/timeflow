



##################
# Read pkg_info
##################

import json
from os.path import dirname

with open(dirname(__file__) + '/pkg_info.json') as fp:
    _info = json.load(fp)

__version__ = _info['version']

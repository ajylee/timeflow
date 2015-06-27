

##################
# Main interface
##################

from .td_mapping import (
    DerivedDictionary, StepMapping, DerivedMapping
)

from .td_set import (
    DerivedSet, StepSet
)

from .base import (
    TimeLine, now
)




##################
# Read pkg_info
##################

import json as _json
from os.path import dirname as _dirname

with open(_dirname(__file__) + '/pkg_info.json') as fp:
    _info = _json.load(fp)

__version__ = _info['version']

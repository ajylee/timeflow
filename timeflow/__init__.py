

##################
# Main interface
##################

from .td_mapping import (
    SnapshotMapping,
    MappingFlow
)

from .td_set import (
    DerivedSet, StepSet, SnapshotSet
)

from .base import (
    TimeLine, StepLine, now, Plan
)

from .flow import Flow

from .event import Event


##################
# Read pkg_info
##################

import json as _json
from os.path import dirname as _dirname

with open(_dirname(__file__) + '/pkg_info.json') as fp:
    _info = _json.load(fp)

__version__ = _info['version']

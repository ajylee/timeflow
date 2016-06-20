

##################
# Main interface
##################

from .td_mapping import (
    MappingFlow,
    BridgeMappingFlow,
)

from .td_set import (
    SetFlow,
    BridgeSetFlow,
)

from .timeline import TimeLine, StepLine, now

from .plan import Plan

from .flow import SimpleFlow

from .event import Event

from .convenience import introduce

# for handling diffs
from .linked_structure import DIFF_LEFT, DIFF_RIGHT, NO_VALUE, diff


##################
# Read pkg_info
##################

import json as _json
from os.path import dirname as _dirname

with open(_dirname(__file__) + '/pkg_info.json') as fp:
    _info = _json.load(fp)

__version__ = _info['version']

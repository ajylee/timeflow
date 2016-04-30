

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

# TODO: maybe delete this module

import collections

from .plan import Plan
from .td_mapping import MappingFlow
from .td_set import SetFlow

# maps base types to flow types
flow_types = {collections.Set: SetFlow,
              set: SetFlow,
              collections.Mapping: MappingFlow,
              dict: MappingFlow}


def introduce(plan, initial_value):
    """Convenience method for calling Flow.introduce_at"""
    _flow = flow_types[type(initial_value)]()
    _flow.at(plan).update(initial_value)
    return _flow

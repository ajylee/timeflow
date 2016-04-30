import collections
import itertools
from .flow import Flow
from .linked_mapping import empty_linked_mapping

delete = ('delete', object)


class MappingFlow(Flow):
    default = empty_linked_mapping

    
class BridgeMappingFlow(MappingFlow, collections.Mapping):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, timeline, initial_value):
        self.timeline = timeline
        plan = self.timeline.new_plan()
        self.at(plan).update(initial_value)
        self.timeline.commit(plan)

    # drop-in convenience methods
    # ############################

    def __getitem__(self, key):
        return self.at(self.timeline.HEAD)[key]

    def __iter__(self):
        return iter(self.at(self.timeline.HEAD))

    def __len__(self):
        return len(self.at(self.timeline.HEAD))

    def __repr__(self):
        return repr(self.at(self.timeline.HEAD))

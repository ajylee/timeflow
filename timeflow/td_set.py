import collections
import itertools
from .linked_set import empty_linked_set
from .flow import StructureFlow


class SetFlow(StructureFlow):
    default = empty_linked_set


class BridgeSetFlow(SetFlow, collections.Set):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, timeline):
        self.timeline = timeline

    # drop-in convenience methods
    # ############################

    @property
    def head(self):
        return self.at(self.timeline.HEAD)

    def __contains__(self, element):
        return self.head.__contains__(element)

    def __iter__(self):
        return iter(self.head)

    def __len__(self):
        return len(self.head)

    def __repr__(self):
        return object.__repr__(self) + repr(self.head)

    def intersection(self, other):
        return set(self.head).intersection(set(other))

    def union(self, other):
        return self.head.__or__(other)

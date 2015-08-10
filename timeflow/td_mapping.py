import collections
import itertools
from .base import DerivedObject, DerivedStage
from .flow import Flow
from .linked_mapping import empty_linked_mapping

delete = ('delete', object)


class StepMapping(Flow, collections.Mapping):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, base_mapping):
        self.head = SnapshotMapping(base_mapping)

    # drop-in convenience methods
    # ############################

    def __getitem__(self, key):
        return self.head[key]

    def __iter__(self):
        return iter(self.head)

    def __len__(self):
        return len(self.head)

    def __repr__(self):
        return repr(self.head)


class MappingFlow(Flow):
    default = empty_linked_mapping



# Aliases
# ################################################################################


def SnapshotMapping(base, copy=True):
    modifications = {}

    if copy:
        return DerivedMapping(base.copy(), modifications=modifications)
    else:
        return DerivedMapping(base, modifications=modifications)

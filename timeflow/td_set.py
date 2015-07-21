import collections
import itertools
from .base import StepFlow, DerivedObject, DerivedStage


def apply_modifications(base, additions, removals):
    base.update(additions)
    base.difference_update(removals)


class DerivedSet(collections.Set, DerivedObject):
    def __init__(self, base, additions=None, removals=None):
        # base is a Mapping. (Could even be another DerivedMapping)
        self._base = base
        self._additions = set() if additions is None else additions
        self._removals = set() if removals is None else removals

    def __iter__(self):
        # NB self._base does not intersect with self._additions, therefore
        # iterator will not yield duplicates.
        return itertools.chain(self._additions,
                               (elt for elt in self._base if elt not in self._removals))

    def __len__(self):
        return len(self._base) + len(self._additions) - len(self._removals)

    def __repr__(self):
        return set(self).__repr__()

    def __contains__(self, element):
        return (
            (element in self._base or element in self._additions)
            and element not in self._removals)

    def new_stage(self):
        return DerivedMutableSet(self, None, None)

    # cache controlling methods
    def rebase(self, new_base):
        """Change dependency on base.

        This method only affects efficiency.

        """

        new_additions = self - new_base
        new_removals = new_base - self
        self._base = new_base
        self._additions = new_additions
        self._removals = new_removals

    def _reroot_base(bs1, bs2):
        """For efficiency only. Mutates bs1._base. Make sure nothing refers to
        it.

        Involves implementation details of DerivedSet.

        """

        root_base = bs1._base
        assert not (bs1._additions or bs1._removals)

        bs1._additions, bs1._removals = bs2._removals, bs2._additions
        bs1._base = bs2

        apply_modifications(root_base, bs2._additions, bs2._removals)
        bs2._additions = set()
        bs2._removals = set()
        bs2._base = root_base


class DerivedMutableSet(DerivedSet, DerivedStage, collections.MutableSet):
    def add(self, element):
        # NB self._base contains self._removals
        if element not in self._base:
            self._additions.add(element)

    def discard(self, element):
        if element in self._base:
            self._removals.add(element)
        elif element in self._additions:
            self._additions.remove(element)

    def frozen_view(self):
        return DerivedSet(self._base, self._additions, self._removals)

    def update(self, other):
        for elt in other:
            self.add(elt)


class StepSet(StepFlow, collections.Set):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, base_set=None):
        if base_set is None:
            base_set = set()
        self.head = DerivedSet(base_set)


    # drop-in convenience methods
    # ############################

    def __contains__(self, element):
        return self.head.__contains__(element)

    def __iter__(self):
        return iter(self.head)

    def __len__(self):
        return len(self.head)

    def __repr__(self):
        return repr(self.head)

    def intersection(self, other):
        return self.head.__and__(other)

    def union(self, other):
        return self.head.__or__(other)



# Aliases
# ################################################################################


def SnapshotSet(base, copy=True):
    if copy:
        return DerivedSet(base.copy(), additions=None, removals=None)
    else:
        return DerivedSet(base, additions=None, removals=None)

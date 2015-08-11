import collections
import itertools
import weakref
from linked_structure import PARENT, CHILD, SELF, EmptyMapping, empty_mapping, LinkedStructure


class LinkedSet(LinkedStructure, collections.Set):
    def __contains__(self, k):
        try:
            return self.diff_base[k] is self.diff_side
        except KeyError:
            return k in self.base

    def __iter__(self):
        return itertools.chain(
            (k for k,v in self.diff_base.iteritems() if v is self.diff_side),
            (k for k in self.base if k not in self.diff_base))

    def __len__(self):
        count = len(self.base)
        for k,v in self.diff_base.iteritems():
            if v is self.diff_side:
                count += 1
            else:
                count -= 1
        return count

    def egg(self):
        return LinkedMutableSet(self, {}, self, PARENT)

    @staticmethod
    def _update_core(core, target):
        for k,v in target.diff_base.items():
            if v is target.diff_side:
                core.add(k)
            else:
                core.remove(k)


class LinkedMutableSet(LinkedSet, collections.MutableSet):
    """Mutable version of LinkedSet, with restrictions

    The LinkedDictionary cannot have children. In particular,
    its `base_relation` cannot be CHILD. This assumption simplifies
    implementation.

    """

    def add(self, k):
        if self.base_relation is SELF:
            self.base.add(k)

        # NB cannot have children
        if self.parent():
            if k not in self.parent():
                self.diff_parent[k] = 1
            else:
                self.diff_parent.pop(k, None)

    def discard(self, k):
        if self.base_relation is SELF:
            self.base.discard(k)

        # NB cannot have children
        if self.parent():
            if k in self.parent():
                self.diff_parent[k] = 0
            else:
                self.diff_parent.pop(k, None)


    def update(self, other):
        for elt in other:
            self.add(elt)


    def hatch(self):
        hatched = LinkedSet(self.parent(), self.diff_parent, self.base, self.base_relation)

        # make self unusable; references to self should be deleted so memory can be reclaimed.
        # NB we cannot simply delete these attrs -- LinkedMapping.__del__ will make warnings.
        self.base = frozenset()
        self.diff_base = empty_mapping

        return hatched


def first_egg(base):
    return LinkedMutableSet(None, None, base, SELF)


class EmptyLinkedSet(frozenset):
    def __init__(self):
        pass

    @staticmethod
    def __contains__(key):
        return False

    @staticmethod
    def __iter__():
        return iter(())

    @staticmethod
    def __len__():
        return 0

    def egg(self):
        return first_egg({})


empty_linked_set = EmptyLinkedSet()

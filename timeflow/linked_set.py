import collections
import itertools
import weakref
from .event import empty_ref
from .linked_structure import (SELF, EmptyMapping, empty_mapping, LinkedStructure,
                               PARENT, CHILD, DIFF_LEFT, DIFF_RIGHT)


class LinkedSet(LinkedStructure, collections.Set):
    # mutable_variant is set after LinkedMutableSet is defined

    def __contains__(self, k):
        try:
            return self.diff_base[k] is self.relation_to_base
        except KeyError:
            return k in self.base

    def __iter__(self):
        return itertools.chain(
            (k for k,v in self.diff_base.iteritems() if v is self.relation_to_base),
            (k for k in self.base if k not in self.diff_base))

    def __len__(self):
        count = len(self.base)
        for k,v in self.diff_base.iteritems():
            if v is self.relation_to_base:
                count += 1
            else:
                count -= 1
        return count

    @staticmethod
    def _update_core(core, target):
        """Make core equal to target (as sets)"""

        # Add elts that are in target but not in core to core.
        # Remove elts that are in core but not in target from core.
        for k,v in target.diff_base.items():
            if v is target.relation_to_base:
                core.add(k)
            else:
                core.remove(k)

    @staticmethod
    def _reverse_diff(item):
        val, diff_side = item
        return (val, (diff_side + 1) % 2)

    @staticmethod
    def _diff(left, right):
        return itertools.chain(((val, DIFF_LEFT) for val in left if val not in right),
                               ((val, DIFF_RIGHT) for val in right if val not in left))

    def __repr__(self):
        return '{}({})'.format(repr(type(self)), repr(list(self)))

    def __and__(self, other):
        return self.intersection(other)

    def __or__(self, other):
        return self.union(other)

    def intersection(self, other):
        if len(self) > len(other):
            larger, smaller = self, other
        else:
            larger, smaller = other, self

        return frozenset(elt for elt in smaller if elt in larger)

    def union(self, other):
        return frozenset(itertools.chain(self, other))


class LinkedMutableSet(LinkedSet, collections.MutableSet):
    """Mutable version of LinkedSet, with restrictions

    The LinkedDictionary cannot have children. In particular,
    its `relation_to_base` cannot be PARENT. This assumption simplifies
    implementation.

    """

    def add(self, k):
        if self.relation_to_base is SELF:
            self.base.add(k)

        # NB cannot have children
        if self.parent() is not None:
            if k not in self.parent():
                self.diff_parent[k] = CHILD
            else:
                self.diff_parent.pop(k, None)

    def discard(self, k):
        if self.relation_to_base is SELF:
            self.base.discard(k)

        # NB cannot have children
        if self.parent() is not None:
            if k in self.parent():
                self.diff_parent[k] = PARENT
            else:
                self.diff_parent.pop(k, None)


    def update(self, other):
        for elt in other:
            self.add(elt)


    def hatch(self):
        hatched = LinkedSet(self.parent(), self.diff_parent, self.base, self.relation_to_base)

        # make self unusable; references to self should be deleted so memory can be reclaimed.
        # NB we cannot simply delete these attrs -- LinkedMapping.__del__ will make warnings.
        del self.base
        del self.diff_base

        return hatched


LinkedSet.mutable_variant = LinkedMutableSet
LinkedMutableSet.immutable_variant = LinkedSet


class EmptyLinkedSet(frozenset):

    def __init__(self):
        self.parent = empty_ref

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
        return LinkedSet.first_egg(set())


empty_linked_set = EmptyLinkedSet()

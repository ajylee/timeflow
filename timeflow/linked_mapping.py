import collections
import itertools
import weakref
from .ref_tools import empty_ref
from .linked_structure import (CHILD, SELF, NO_VALUE, EmptyMapping,
                               empty_mapping, LinkedStructure, DIFF_LEFT, DIFF_RIGHT,
                               hatch_egg_optimized)


class EmptyLinkedMapping(EmptyMapping):

    def __init__(self):
        self.parent = empty_ref
        self.relation_to_base = SELF

    def egg(self):
        return LinkedMapping.first_egg({})

empty_linked_mapping = EmptyLinkedMapping()


class LinkedMapping(LinkedStructure, collections.Mapping):

    core_type = dict
    empty_variant = empty_linked_mapping

    def __init__(self, parent, diff_parent, base, relation_to_base):
        assert not isinstance(parent, collections.MutableMapping)
        LinkedStructure.__init__(self, parent, diff_parent, base, relation_to_base)

    def __getitem__(self, k):
        try:
            val = self.diff_base[k][self.relation_to_base]
        except KeyError:
            try:
                return self.base[k]
            except KeyError:
                raise KeyError

        if val == NO_VALUE:
            raise KeyError
        else:
            return val

    def __iter__(self):
        return itertools.chain(
            (k for k,v in self.diff_base.iteritems() if v[self.relation_to_base] != NO_VALUE),
            (k for k in self.base if k not in self.diff_base))

    def __len__(self):
        count = len(self.base)
        for k,v in self.diff_base.iteritems():
            if v[self.relation_to_base] is NO_VALUE:
                count -= 1
            elif k not in self.base:
                count += 1
        return count

    @staticmethod
    def _update_core(core, target):
        for k,v in target.diff_base.items():
            target_val = v[target.relation_to_base]
            if target_val is NO_VALUE:
                del core[k]
            else:
                core[k] = target_val

    @staticmethod
    def _reverse_diff(item):
        key, val = item
        return (key, (val[1], val[0]))

    @staticmethod
    def _diff(left, right):
        for key, left_val in left.iteritems():
            right_val = right.get(key, NO_VALUE)
            if left_val != right_val:
                yield (key, (left_val, right_val))

        for key, right_val in right.iteritems():
            if key not in left:
                yield (key, (NO_VALUE, right_val))

    def __repr__(self):
        return '{}({})'.format(repr(type(self)), repr(dict(self)))


class LinkedDictionary(LinkedMapping, collections.MutableMapping):
    """Mutable version of LinkedMapping, with restrictions

    The LinkedDictionary cannot have children. In particular,
    its `relation_to_base` cannot be PARENT. This assumption simplifies
    implementation.

    """

    def __setitem__(self, k, v):
        # cannot have children
        if self.parent() is not None:
            parent_value = self.parent().get(k, NO_VALUE)
            if parent_value != v:
                self.diff_parent[k] = (parent_value, v)
            else:
                self.diff_parent.pop(k, None)

        if self.relation_to_base is SELF:
            self.base[k] = v

    def __delitem__(self, k):
        # cannot have children
        if self.relation_to_base is SELF:
            try:
                del self.base[k]
            except KeyError:
                raise KeyError

        if self.parent() is not None:
            if self.diff_parent.get(k, (None, None))[CHILD] is NO_VALUE:
                raise KeyError
            else:
                try:
                    self.diff_parent[k] = (self.parent()[k], NO_VALUE)
                except KeyError:
                    # parent has no such key => key in self.diff_parent or KeyError
                    try:
                        del self.diff_parent[k]
                    except KeyError:
                        raise KeyError, 'no such key'


    hatch = hatch_egg_optimized


LinkedMapping.mutable_variant = LinkedDictionary
LinkedDictionary.immutable_variant = LinkedMapping

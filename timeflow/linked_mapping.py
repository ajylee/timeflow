import collections
import itertools
import weakref
from linked_structure import CHILD, SELF, delete, EmptyMapping, empty_mapping, LinkedStructure


class LinkedMapping(LinkedStructure, collections.Mapping):

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

        if val == delete:
            raise KeyError
        else:
            return val

    def __iter__(self):
        return itertools.chain(
            (k for k,v in self.diff_base.iteritems() if v[self.relation_to_base] != delete),
            (k for k in self.base if k not in self.diff_base))

    def __len__(self):
        count = len(self.base)
        for k,v in self.diff_base.iteritems():
            if v[self.relation_to_base] is delete:
                count -= 1
            elif k not in self.base:
                count += 1
        return count

    @staticmethod
    def _update_core(core, target):
        for k,v in target.diff_base.items():
            target_val = v[target.relation_to_base]
            if target_val is delete:
                del core[k]
            else:
                core[k] = target_val

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
            parent_value = self.parent().get(k, delete)
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
            if self.diff_parent.get(k, (None, None))[CHILD] is delete:
                raise KeyError
            else:
                try:
                    self.diff_parent[k] = (self.parent()[k], delete)
                except KeyError:
                    # parent has no such key => key in self.diff_parent or KeyError
                    try:
                        del self.diff_parent[k]
                    except KeyError:
                        raise KeyError, 'no such key'


    def hatch(self):
        hatched = LinkedMapping(self.parent(), self.diff_parent, self.base, self.relation_to_base)

        # make self unusable; references to self should be deleted so memory can be reclaimed.
        # NB we cannot simply delete these attrs -- LinkedMapping.__del__ will make warnings.
        self.base = empty_mapping
        self.diff_base = empty_mapping

        return hatched


LinkedMapping.mutable_variant = LinkedDictionary


class EmptyLinkedMapping(EmptyMapping):
    def egg(self):
        return LinkedMapping.first_egg({})


empty_linked_mapping = EmptyLinkedMapping()

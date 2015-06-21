import collections
import itertools
import toolz as tz
from operator import ne

delete = ('delete', object)
no_element = ('no_element', object)


def chain_getitem(mappings, key):
    """Search through an Iterable of mappings for key, and return its value.

    If key is in multiple mappings, return value in earliest mapping.

    """
    for mm in mappings:
        try:
            return mm[key]
        except KeyError:
            continue
    else:
        raise KeyError


def apply_modifications(base, modifications):
    for k, v in modifications.iteritems():
        if v == delete:
            del base[k]
        else:
            base[k] = v


def reversed_modifications(base, modifications):
    _out = {}
    for k in modifications:
        base_v = base.get(k, no_element)
        if base_v is no_element:
            # assert v is not delete  # debug
            _out[k] = delete
        else:
            # assert v != base_v      # debug
            _out[k] = base[k]

    return _out


class BasedMapping(collections.Mapping):

    def __init__(self, base, mapping=None):
        # base is a Mapping. (Could even be another BasedMapping)
        self._base = base
        self._modifications = {}

        if mapping is not None:
            for k in set(base) - set(mapping):
                self._modifications[k] = delete

            for k,v in mapping.iteritems():
                if base.get(k, no_element) != v:
                    self._modifications[k] = v

    def __getitem__(self, key):
        try:
            val = chain_getitem((self._modifications, self._base), key)
        except KeyError:
            raise KeyError

        if val is delete:
            raise KeyError

        return val

    def __iter__(self):
        return itertools.chain(
            (k for k,v in self._modifications.iteritems() if v != delete),
            (k for k in self._base if k not in self._modifications))

    def __len__(self):
        count = len(self._base)
        for k,v in self._modifications.iteritems():
            if k is delete:
                count -= 1
            elif k not in self._base:
                count += 1
        return count

    def __repr__(self):
        return dict(self).__repr__()

    # cache controlling methods
    def rebase(self, new_base):
        """Change dependency on base.

        This method only affects efficiency.

        """

        new_self_proxy = BasedMapping(new_base, self)
        self._base = new_base
        self._modifications = new_self_proxy._modifications

    def _reroot_base(bm1, bm2):
        """For efficiency only. Mutates bm1._base. Make sure nothing refers to
        it.

        Involves implementation details of BasedMapping.

        """

        root_base = bm1._base
        assert not bm1._modifications

        bm1._modifications = reversed_modifications(root_base, bm2._modifications)
        bm1._base = bm2

        apply_modifications(root_base, bm2._modifications)
        bm2._modifications.clear()
        bm2._base = root_base


class BasedDictionary(BasedMapping):
    def __delitem__(self, key):
        # NB never modifies the base mapping
        if self._modifications.get(key) is delete:
            raise KeyError

        in_modifications = key in self._modifications
        in_base = key in self._base

        if in_base:
            self._modifications[key] = delete
        elif in_modifications: # not in_base
            del self._modifications[key]
        else:
            raise KeyError, "no such key {}".format(key)

    def __setitem__(self, key, value):
        # NB never modifies the base mapping
        if self._base.get(key, no_element) != value:
            self._modifications[key] = value
        else:
            try:
                del self._modifications[key]
            except KeyError:
                pass


class FrozenMapping(collections.Mapping):
    def __init__(self, base):
        self._base = base

    def __getitem__(self, key):
        return self._base

    def __iter__(self, key):
        return iter(self._base)

    def __len__(self):
        return len(self._base)


class StepDictionary(object):
    """Drop in replacement for a regular Dict"""
    def __init__(self, base_dictionary):
        self.head = base_dictionary
        self.stage = BasedDictionary(self.head)

    def commit(self):
        apply_modifications(self.head, self.stage._modifications)
        self.stage._modifications.clear()

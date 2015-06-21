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

    # cache controlling methods
    def rebase(self, new_base):
        """Change dependency on base. You could also set new_base to self to make it independent!

        This method only affects efficiency.

        """

        new_self_proxy = BasedMapping(new_base, self)
        self._base = new_base
        self._modifications = new_self_proxy._modifications


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
        self._modifications[key] = value


class FrozenMapping(collections.Mapping):
    def __init__(self, base):
        self._base = base

    def __getitem__(self, key):
        return self._base

    def __iter__(self, key):
        return iter(self._base)

    def __len__(self):
        return len(self._base)


class StepMapping(object):
    def __init__(self, current_mapping):
        self.now = current_mapping
        self.future = BasedDictionary(self.now, self.now)

    def step(self):
        return StepMapping(self.future)

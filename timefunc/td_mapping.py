import collections
import itertools
import toolz as tz

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
    def __init__(self, base):
        # base is a Mapping. Could be another ModifiedDictionary
        self._base = base
        self._create = {}
        self._update = {}
        self._delete = set()

    def __getitem__(self, key):
        if key in self._delete:
            raise KeyError
        else:
            try:
                return chain_getitem((self._create, self._update, self._base), key)
            except KeyError:
                raise KeyError

    def __iter__(self):
        return itertools.chain(
            iter(self._create),
            iter(self._update),
            (k for k in self._base if k not in self._delete))

    def __len__(self):
        return len(self._base) - len(self._delete) + len(self._create)

    # cache controlling methods
    def rebase(self, new_base):
        """Change dependency on base"""
        new_self = BasedMapping(new_base)
        for k,v in self.iteritems():
            if k not in new_base:


class BasedDictionary(BasedMapping):
    def __delitem__(self, key):
        # NB never modifies the base mapping
        if key in self._delete:
            raise KeyError
        elif key in self._create:
            del self._create[key]
        elif key in self._update:
            del self._update[key]
            self._delete.add(key)
        elif key in self._base:
            self._delete.add(key)
        else:
            raise KeyError

    def __setitem__(self, key, value):
        # NB never modifies the base mapping
        if key in self._delete:
            self._delete.remove(key)
            if self._base[key] != value:
                self._update[key] = value
        elif key in self._update:
            if self._base[key] != value:
                self._update[key] = value
            else:
                del self._update[key]
        elif key in self._base:
            if self._base[key] != value:
                self._update[key] = value
        else:
            # key either in self._create or not in any of _create, _update, _delete, _base
            self._create[key] = value

    def __repr__(self):
        return dict(self).__repr__()
        


class FrozenMapping(collections.Mapping):
    def __init__(self, base):
        self._base = base

    def __getitem__(self, key):
        return self._base

    def __iter__(self, key):
        return iter(self._base)

    def __len__(self):
        return len(self._base)


class TDMapping(object):
    def __init__(self, current_mapping, current_time):
        self.now = current_mapping
        self.future = BasedDictionary(self.now)

    def step(self):
        return TDMapping(self.future)

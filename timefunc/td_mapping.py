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

    def __init__(self, base, mapping=None):
        # base is a Mapping. (Could even be another BasedMapping)
        self._base = base
        self._create = {}
        self._update = {}

        if mapping is not None:
            self._delete = set(base) - set(mapping)
            for k,v in mapping.iteritems():
                if k in base:
                    self._update[k] = v
                else:
                    self._create[k] = v
        else:
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
        """Change dependency on base. You could also set new_base to self to make it independent!

        This method only affects efficiency.

        """

        new_self_proxy = BasedMapping(new_base, self)
        self._base = new_base
        self._create = new_self_proxy._create
        self._update = new_self_proxy._update
        self._delete = new_self_proxy._delete


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


class StepMapping(object):
    def __init__(self, current_mapping):
        self.now = current_mapping
        self.future = BasedDictionary(self.now, self.now)

    def step(self):
        return StepMapping(self.future)

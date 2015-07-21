import collections
import itertools
import toolz as tz
from operator import ne
from .base import StepFlow, TimeLine, DerivedObject, DerivedStage, now

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


def derive_modifications(base, mapping):
    _modifications = {}
    for k in set(base) - set(mapping):
        _modifications[k] = delete

    for k,v in mapping.iteritems():
        if base.get(k, no_element) != v:
            _modifications[k] = v


class DerivedMapping(collections.Mapping, DerivedObject):

    def __init__(self, base, modifications=None):
        # base is a Mapping. (Could even be another DerivedMapping)
        self._base = base
        self._modifications = {} if modifications is None else modifications

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

    def new_stage(self):
        return DerivedDictionary(self)

    # cache controlling methods
    def rebase(self, new_base):
        """Change dependency on base.

        This method only affects efficiency.

        """

        new_modifications = derive_modifications(new_base, self)
        self._base = new_base
        self._modifications = new_modifications

    def _reroot_base(bm1, bm2):
        """For efficiency only. Mutates bm1._base. Make sure nothing refers to
        it.

        Involves implementation details of DerivedMapping.

        """

        root_base = bm1._base
        assert not bm1._modifications

        bm1._modifications = reversed_modifications(root_base, bm2._modifications)
        bm1._base = bm2

        apply_modifications(root_base, bm2._modifications)
        bm2._modifications.clear()
        bm2._base = root_base

    def _apply_modifications(self, base):
        apply_modifications(base, self._modifications)


class DerivedDictionary(DerivedMapping, DerivedStage, collections.MutableMapping):
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

    def frozen_view(self):
        return DerivedMapping(self._base, self._modifications)


class DerivedDefaultDictionary(DerivedDictionary):
    def __init__(self, base, modifications, default_thunk):
        DerivedDictionary.__init__(self, base, modifications)
        self._default_thunk = default_thunk

    def __getitem__(self, key):
        try:
            return DerivedDictionary.__getitem__(self, key)
        except KeyError:
            _default = self._default_thunk()
            self.__setitem__(self, key, _default)
            return _default


class FrozenMappingLayer(collections.Mapping):
    def __init__(self, base):
        self._base = base

    def __getitem__(self, key):
        return self._base[key]

    def __iter__(self):
        return iter(self._base)

    def __len__(self):
        return len(self._base)

    def __repr__(self):
        return dict(self).__repr__()

    def new_stage(self):
        return DerivedDictionary(self._base)


class StepMapping(FrozenMappingLayer, StepFlow):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, base_dictionary):
        self.head = FrozenMappingLayer(base_dictionary)
        self._base = base_dictionary

    def __hash__(self):
        return object.__hash__(self)


class StepDefaultMapping(StepMapping):
    """Similar to StepMapping, but allows defaultdict functionality for the stage"""

    def __init__(self, base_dictionary, default_thunk):
        self.head = FrozenMappingLayer(base_dictionary)
        self._base = base_dictionary
        self._default_thunk = default_thunk

    def new_stage(self):
        return DerivedDefaultDictionary(base = self._base,
                                        modifications = None,
                                        default_thunk = self._default_thunk)



# Aliases
# ################################################################################


def SnapshotMapping(base, copy=True):
    if copy:
        return DerivedMapping(base.copy())
    else:
        return DerivedMapping(base)

import collections
import itertools
from .base import TimeLine, DerivedObject, DerivedStage, TDItem

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


class DerivedMapping(DerivedObject, collections.Mapping):

    def __init__(self, base, modifications):
        # base is a Mapping. (Could even be another DerivedMapping)
        self._base = base
        self._modifications = modifications

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
        return DerivedDictionary(self, modifications={})

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

    def frozen_view(self):
        if len(self) > 0:
            return self
        else:
            return empty_mapping


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


class StepMapping(TDItem, collections.Mapping):
    """Drop in replacement for a regular Dict

    Obtain data from :attr:`head`. Head cannot be modified directly via the
    public API; instead, modify :attr:`stage`, then commit. This applies
    modifications to head.

    """

    def __init__(self, base_mapping):
        self.head = SnapshotMapping(base_mapping)

    # drop-in convenience methods
    # ############################

    def __getitem__(self, key):
        return self.head[key]

    def __iter__(self):
        return iter(self.head)

    def __len__(self):
        return len(self.head)

    def __repr__(self):
        return repr(self.head)


class EmptyMapping(DerivedMapping):
    def __init__(self):
        pass

    @staticmethod
    def __getitem__(key):
        raise KeyError

    @staticmethod
    def __iter__():
        return iter(())

    @staticmethod
    def __len__():
        return 0

    def _reroot_base(self, other):
        other._base = other._modifications
        other._modifications = {}


empty_mapping = EmptyMapping()


class MappingFlow(TDItem):
    default = empty_mapping



# Aliases
# ################################################################################


def SnapshotMapping(base, copy=True):
    modifications = {}

    if copy:
        return DerivedMapping(base.copy(), modifications=modifications)
    else:
        return DerivedMapping(base, modifications=modifications)

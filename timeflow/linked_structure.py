import six
from abc import abstractmethod, ABCMeta
import weakref
import collections
import uuid
import itertools
import logging

import toolz

logger = logging.getLogger(__name__)


NO_VALUE = ('NO_VALUE', uuid.UUID('db62de11-7c24-11e5-91b3-b88d12001ea8'))


PARENT = 0
CHILD = 1
SELF = 2

DIFF_LEFT, DIFF_RIGHT = 0, 1

DEBUG = False

def transfer_core(self, other):
    assert self.relation_to_base is SELF

    core = self.base

    self._update_core(core, other)
    other.set_base(core, SELF)

    if self.parent() is other:
        self.set_base(other, relation_to_base=CHILD)
    else:
        assert other.parent() is self
        self.set_base(other, relation_to_base=PARENT)


class EmptyMapping(collections.Mapping):
    def __init__(self):
        pass

    @staticmethod
    def __getitem__(key):
        raise(KeyError)

    @staticmethod
    def __iter__():
        return iter(())

    @staticmethod
    def __len__():
        return 0


empty_mapping = EmptyMapping()
del EmptyMapping


@six.add_metaclass(ABCMeta)
class LinkedStructure(object):
    """LinkedStructure

    Used create a tree of structures, each represented by diffs from parent or
    child, or directly using a basic python structure (e.g. `set` or `dict`).

    :param LinkedStructure parent:  can also be None
    :param dict diff_parent:        Used iff parent != None
    :param dict base:               Base data
    :param relation_to_base:        PARENT, CHILD, or SELF. Relationship of self to base, e.g.
                                    for CHILD, means self is child of base.


    Attributes
    ----------

    :attr diff_parent:            Dict mapping a key to a difference pair,
                                  (Parent value, self value)
    :attr base:                   Base data, can parent LinkedStructure, a child LinkedStructure,
                                  or an independent basic python structure.


    Memory management
    -----------------

    A LinkedStructure has no strong refs to its parent except for :attr:base .
    :attr:diff_parent is automatically removed if the parent has no strong refs.



    Specs (Incomplete)
    -------------------

    - "~EX a b . (LinkedStructure a) AND a.base == b AND mutable b"

    """

    # A class that adds mutability to the LinkedStructure.
    # Abstract attribute; needs to be set in subclass.
    mutable_variant = None
    core_type = None
    empty_variant = None

    alt_bases = ()  # used in creating/deleting forks.

    def __init__(self, parent, diff_parent, base, relation_to_base):
        weak_self = weakref.ref(self)
        def _del_diff_parent(unused_):
            try:
                weak_self().diff_parent = None
            except AttributeError:
                pass

        self.parent = weakref.ref(parent, _del_diff_parent) if parent is not None else lambda : None
        self.diff_parent = diff_parent
        self.set_base(base, relation_to_base)


    def set_base(self, base, relation_to_base):
        self.base = base
        self.relation_to_base = relation_to_base

        if self.relation_to_base is SELF:
            self.diff_base = empty_mapping
        elif self.relation_to_base is CHILD:
            self.diff_base = self.diff_parent
        elif self.relation_to_base is PARENT:
            self.diff_base = self.base.diff_parent

    @classmethod
    def first_egg(cls, base):
        return cls.mutable_variant(parent=None, diff_parent=None,
                                   base=base, relation_to_base=SELF)


    def egg(self):
        return self.mutable_variant(parent=self, diff_parent={},
                                 base=self, relation_to_base=CHILD)


    @staticmethod
    @abstractmethod
    def _update_core(core, target):
        """Used when transferring core from neighbor to self.

        Mutates the `core` so that `core == target`.

        """
        pass

    @staticmethod
    @abstractmethod
    def _diff(left, right):
        """The diff between two elements of the LinkedStructure subclass

        Format depends on the class.

        """
        pass

    @staticmethod
    @abstractmethod
    def _reverse_diff(item):
        """Reverses left/right polarity of an item from :meth:`_diff`"""
        pass

    def _get_self(self):
        # only used in :prop:`unproxied_base`
        return self

    @property
    def unproxied_base(self):
        return self.base if self.relation_to_base == SELF else self.base._get_self()

    def _remove_alt_base(self, alt_base):
        """Weakref callback for cleaning up dead alt_base ref

        :param weakref.ReferenceType alt_base: weakref to an alt base

        """
        self.alt_bases = tuple(_elt for _elt in self.alt_bases
                            if _elt is not alt_base)

        if not self.alt_bases:
            del self.alt_bases
            if type(self.base) is weakref.ProxyType:
                self.base = self.unproxied_base


    def __del__(self):
        # search up to

        if type(self) is self.mutable_variant:
            # no structure other than `self` should be based on the mutable variant
            return

        _parent = self.parent()

        try:
            if _parent.relation_to_base != PARENT:
                return
        except AttributeError:
            # should only happen if _parent is None
            return

        try:
            _base = _parent.unproxied_base
        except ReferenceError as exc:
            # Parent has no base; need to get it a new one. (this shouldn't happen though.)
            logger.error("{}; `_parent.base` is missing. Shouldn't happen, but continuing with new base."
                         .format(exc), exc_info=True)
            pass
        else:
            if _base is not self:
                # _parent.base should be another child; no need to do anything
                return

        if _parent.alt_bases:
            # set _parent base to an alternative
            new_base = _parent.alt_bases[0]()

            # figure relation of _parent to new_base
            if new_base.parent() is _parent:
                relation_to_base = PARENT
            elif _parent.parent() is new_base:
                relation_to_base = CHILD
            else:
                raise ValueError("invalid relation_to_base")

            _parent.set_base(new_base, relation_to_base)

            _rest_alt_bases = _parent.alt_bases[1:]
            if not _rest_alt_bases:
                del _parent.alt_bases
            else:
                _parent.alt_bases = _rest_alt_bases
                _parent.base = weakref.proxy(_parent.base)
        else:
            # move core to parent
            _path = walk_to_core(self)
            _path.reverse()  # now _path is from core to self
            for ls1, ls2 in toolz.sliding_window(2, itertools.chain(_path, (_parent,))):
                transfer_core(ls1, ls2)


def hatch_egg_simple(egg):
    hatched = egg.immutable_variant(
        egg.parent(), egg.diff_parent,
        egg.unproxied_base, egg.relation_to_base)

    # make egg unusable; references to
    # egg should be deleted so memory can be reclaimed.
    del egg.base
    del egg.diff_base

    return hatched


def hatch_egg_optimized(egg: LinkedStructure, debug_label_suffix='c'):
    """Hatch egg, optimizing memory management

    egg needs to be a mutable variant of the LinkedStructure
    """
    # TODO: rename this func to "hatch_egg_and_manage_memory"

    if egg == egg.empty_variant:
        return egg.empty_variant
    elif egg.relation_to_base is CHILD and len(egg.diff_base) == 0:
        # The egg is a NOP.
        # NOTE: If egg.relation_to_base is SELF, then `len(egg.diff_base) == 0`
        # trivially and tells us nothing.

        # make egg unusable; references to
        # egg should be deleted so memory can be reclaimed.
        del egg.base
        del egg.diff_base
        return egg.parent()
    else:
        _parent = egg.parent()
        hatched = egg.immutable_variant(
            _parent, egg.diff_parent,
            egg.unproxied_base, egg.relation_to_base)

        # make egg unusable; references to
        # egg should be deleted so memory can be reclaimed.
        del egg.base
        del egg.diff_base

        if hatched.relation_to_base == CHILD:
            if _parent.relation_to_base is SELF:
                transfer_core(_parent, hatched)
                if DEBUG:
                    hatched.debug_label = getattr(_parent, 'debug_label', str(id(_parent))) + '.' + debug_label_suffix
                    _parent_label = getattr(_parent, 'debug_label', id(_parent))
                    logger.debug('transferred core %s -> %s', _parent_label, hatched.debug_label)
            else:
                # creating a fork
                if DEBUG:
                    hatched.debug_label = getattr(_parent, 'debug_label', str(id(_parent))) + '.' + debug_label_suffix
                    logger.debug('creating a fork, parent.relation_to_base: {}, parent: {}, hatched: {}, parent.base: {}'
                                 .format(
                                     {CHILD:'CHILD', PARENT:'PARENT', SELF:'SELF'}[_parent.relation_to_base],
                                     getattr(_parent, 'debug_label', id(_parent)),
                                     hatched.debug_label,
                                     getattr(_parent.base, 'debug_label', id(_parent.unproxied_base)),
                                 ))

                create_core_in(hatched)
                if type(_parent.base) is not weakref.ProxyType:
                    _parent.base = weakref.proxy(_parent.base)
                _parent.alt_bases += (
                    weakref.ref(hatched, _parent._remove_alt_base),)

        return hatched


def create_core_in(linked_structure):
    linked_structure.base = linked_structure.core_type(linked_structure)
    linked_structure.diff_base = empty_mapping
    linked_structure.relation_to_base = SELF


def walk_to_core(linked_structure):
    path = [linked_structure]
    while path[-1].relation_to_base != SELF:
        path.append(path[-1].unproxied_base)
    return path


def diff(left: LinkedStructure, right: LinkedStructure):
    if left is right:
        return ()

    elif left.unproxied_base is right:
        # NB: Cannot branch here if (left.relation_to_base is SELF)
        if left.relation_to_base is PARENT:
            return left.diff_base.items()
        else:
            return (left._reverse_diff(item)
                    for item in left.diff_base.items())

    elif right.unproxied_base is left:
        # NB: Cannot branch here if (left.relation_to_base is SELF)
        if right.relation_to_base is CHILD:
            return right.diff_base.items()
        else:
            return (right._reverse_diff(item) for item in
                    right.diff_base.items())

    else:
        return left._diff(left, right)

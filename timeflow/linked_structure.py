from abc import abstractmethod
import weakref
import collections
import uuid

NO_VALUE = ('NO_VALUE', uuid.UUID('db62de11-7c24-11e5-91b3-b88d12001ea8'))


PARENT = 0
CHILD = 1
SELF = 2

DIFF_LEFT, DIFF_RIGHT = 0, 1


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
        raise KeyError

    @staticmethod
    def __iter__():
        return iter(())

    @staticmethod
    def __len__():
        return 0


empty_mapping = EmptyMapping()


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

    """

    # A class that adds mutability to the LinkedStructure.
    # Abstract attribute; needs to be set in subclass.
    mutable_variant = None


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


def hatch_egg(mutable_variant):
    if mutable_variant == mutable_variant.empty_variant:
        return mutable_variant.empty_variant
    else:
        hatched = mutable_variant.immutable_variant(
            mutable_variant.parent(), mutable_variant.diff_parent,
            mutable_variant.base, mutable_variant.relation_to_base)

        # make mutable_variant unusable; references to mutable_variant should be
        # deleted so memory can be reclaimed.
        del mutable_variant.base
        del mutable_variant.diff_base

        return hatched


def create_core_in(linked_structure):
    linked_structure.base = linked_structure.core_type(linked_structure)
    linked_structure.diff_base = empty_mapping
    linked_structure.relation_to_base = SELF


def diff(left, right):
    if left is right:
        return ()

    elif left.base is right:
        # NB: Cannot branch here if (left.relation_to_base is SELF)
        if left.relation_to_base is PARENT:
            return left.diff_base.iteritems()
        else:
            return (left._reverse_diff(item)
                    for item in left.diff_base.iteritems())

    elif right.base is left:
        # NB: Cannot branch here if (left.relation_to_base is SELF)
        if right.relation_to_base is CHILD:
            return right.diff_base.iteritems()
        else:
            return (right._reverse_diff(item) for item in
                    right.diff_base.iteritems())

    else:
        return left._diff(left, right)

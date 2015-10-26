from abc import abstractmethod
import weakref
import collections

delete = ('delete', object)

PARENT = 0
CHILD = 1
SELF = 2


def transfer_core(self, other):
    assert self.base_relation is SELF

    core = self.base

    self._update_core(core, other)
    other.set_base(core, SELF)

    if self.parent() is other:
        self.set_base(other, PARENT)
    else:
        assert other.parent() is self
        self.set_base(other, CHILD)


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
    :param base_relation:           PARENT, CHILD, or SELF. Relationship of base to self, e.g.
                                    for PARENT, means base is parent of self.


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


    def __init__(self, parent, diff_parent, base, base_relation):
        def _del_diff_parent(unused_):
            self.diff_parent = None

        self.parent = weakref.ref(parent, _del_diff_parent) if parent is not None else lambda : None
        self.diff_parent = diff_parent
        self.set_base(base, base_relation)


    def set_base(self, base, base_relation):
        self.base = base
        self.base_relation = base_relation

        if self.base_relation is SELF:
            self.diff_base = empty_mapping
            self.diff_side = None
        elif self.base_relation is PARENT:
            self.diff_base = self.diff_parent
            self.diff_side = CHILD
        elif self.base_relation is CHILD:
            self.diff_base = self.base.diff_parent
            self.diff_side = PARENT

    @classmethod
    def first_egg(cls, base):
        return cls.mutable_variant(parent=None, diff_parent=None,
                                   base=base, base_relation=SELF)


    def egg(self):
        return self.mutable_variant(parent=self, diff_parent={},
                                 base=self, base_relation=PARENT)


    @staticmethod
    @abstractmethod
    def _update_core(core, target):
        """Used when transferring core from neighbor to self.

        Mutates the `core` so that `core == target`.

        """
        pass

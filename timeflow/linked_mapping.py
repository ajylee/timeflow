import collections
import itertools
import weakref


delete = ('delete', object)

PARENT = 0
CHILD = 1
SELF = 2


class LinkedMapping(collections.Mapping):
    def __init__(self, parent, diff_parent, base, base_relation):
        """LinkedMapping

        Used create a tree of Mappings, each represented by diffs from parent or
        child, or directly using a dict.

        :param LinkedMapping parent:  can also be None
        :param dict diff_parent:      Used iff parent != None
        :param dict base:             Base data
        :param base_relation:         PARENT, CHILD, or SELF. Relationship of base to self, e.g.
                                      for PARENT, means base is parent of self.


        Attributes
        ----------

        :attr diff_parent:            Dict mapping a key to a difference pair,
                                      (Parent value, self value)
        :attr base:                   Base data, can parent LinkedMapping, a child LinkedMapping,
                                      or an independent dictionary.


        Memory management
        -----------------

        A LinkedMapping has no strong refs to its parent except for :attr:base .
        :attr:diff_parent is automatically removed if the parent has no strong refs.

        """

        self.parent = weakref.ref(parent) if parent is not None else lambda : None

        self.del_hooks = []

        self.diff_parent = diff_parent

        if parent is not None:
            assert not isinstance(parent, collections.MutableMapping)
            maybe_self = weakref.ref(self)
            def del_hook():
                if maybe_self():
                    del maybe_self().diff_parent

            parent.del_hooks.append(del_hook)

        self.set_base(base, base_relation)


    def set_base(self, base, base_relation):
        self.base = base
        self.base_relation = base_relation

        if self.base_relation is SELF:
            self.diff_base = {}
            self.diff_side = None
        elif self.base_relation is PARENT:
            self.diff_base = self.diff_parent
            self.diff_side = 1
        elif self.base_relation is CHILD:
            self.diff_base = self.base.diff_parent
            self.diff_side = 0

    def __del__(self):
        if self.parent():
            del self.diff_parent

        for del_hook in self.del_hooks:
            del_hook()

    def __getitem__(self, k):
        try:
            val = self.diff_base[k][self.diff_side]
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
            (k for k,v in self.diff_base.iteritems() if v[self.diff_side] != delete),
            (k for k in self.base if k not in self.diff_base))

    def __len__(self):
        count = len(self.base)
        for k,v in self.diff_base.iteritems():
            if v[self.diff_side] is delete:
                count -= 1
            elif k not in self.base:
                count += 1
        return count

    def egg(self):
        return LinkedDictionary(self, {}, self, PARENT)


class LinkedDictionary(LinkedMapping, collections.MutableMapping):
    """Mutable version of LinkedMapping, with restrictions

    The LinkedDictionary cannot have children. In particular,
    its `base_relation` cannot be CHILD. This assumption simplifies
    implementation.

    """

    def __setitem__(self, k, v):
        # cannot have children
        if self.parent():
            self.diff_parent[k] = (self.parent().get(k, delete), v)

        if self.base_relation is SELF:
            self.base[k] = v

    def __delitem__(self, k):
        # cannot have children
        if self.base_relation is SELF:
            try:
                del self.base[k]
            except KeyError:
                raise KeyError

        if self.parent():
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
        hatched = LinkedMapping(self.parent(), self.diff_parent, self.base, self.base_relation)

        # make self unusable; references to self should be deleted so memory can be reclaimed.
        del self.base
        del self.base_relation
        del self.diff_base

        return hatched


def transfer_core(self, other):
    assert self.base_relation is SELF

    core = self.base

    for k,v in other.diff_base.items():
        if v[other.diff_side] is delete:
            del core[k]
        else:
            core[k] = v[other.diff_side]

    if self.parent() is other:
        self.set_base(other, PARENT)
    else:
        assert other.parent() is self
        self.set_base(other, CHILD)

    other.set_base(core, SELF)


def first_egg(base):
    return LinkedDictionary(None, None, base, SELF)

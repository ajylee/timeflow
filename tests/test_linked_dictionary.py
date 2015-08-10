import collections
import itertools
import weakref
import nose.tools


delete = ('delete', object)

PARENT = 0
CHILD = 1
SELF = 2

def opposite_relation(parent_or_child):
    return 1 - parent_or_child


class LinkedMapping(collections.Mapping):
    def __init__(self, parent, diff_parent, base, base_relation):
        """LinkedMapping

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
            maybe_self = weakref.ref(self)
            def del_hook():
                if maybe_self():
                    del maybe_self().diff_parent

            parent.del_hooks.append(del_hook)

        self.base = base
        self.base_relation = base_relation
        self.set_diff()

    def set_diff(self):
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
        # TODO: delete children's parent refs and diff_parent.
        #del self.parent.diff_child

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
    def __setitem__(self, k, v):
        # cannot have children
        if self.parent():
            self.diff_parent[k] = (self.parent().get(k, delete), v)

        if self.diff_side is None:
            self.base[k] = v

    def __delitem__(self, k):
        # cannot have children
        if self.diff_side is None:
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
    assert self.diff_side is None

    core = self.base

    for k,v in other.diff_base.items():
        if v[other.diff_side] is delete:
            del core[k]
        else:
            core[k] = v[other.diff_side]

    self.base = other
    other.base = core
    other.diff_base = {}
    other.diff_side = None

    if other.parent() is self:
        self.diff_base = other.diff_parent
        self.diff_side = 0
    else:
        self.diff_base = self.diff_parent
        self.diff_side = 1


def first_egg(base):
    return LinkedDictionary(None, None, base, SELF)


@nose.tools.nottest
def setup_tests():
    class X(object):
        pass

    aa_egg = first_egg({})
    aa_egg[1] = 10
    aa_egg['to_delete'] = X()

    aa = aa_egg.hatch()
    del aa_egg

    bb = aa.egg()

    bb[1] = 20
    bb[2] = 30
    del bb['to_delete']

    return aa, bb


def test_linked_dictionary():
    aa, bb = setup_tests()

    assert aa[1] == 10
    assert bb[1] == 20
    assert 2 not in aa


def test_transfer_core():
    aa, bb = setup_tests()
    transfer_core(aa, bb)

    assert aa[1] == 10
    assert bb[1] == 20
    assert 2 not in aa

    transfer_core(bb, aa)

    assert aa[1] == 10
    assert bb[1] == 20
    assert 2 not in aa


def test_memory_management():
    aa, bb = setup_tests()

    assert hasattr(bb, 'diff_parent')
    test_ref = weakref.ref(aa['to_delete'])
    del aa
    assert hasattr(bb, 'diff_parent')
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    assert not hasattr(bb, 'diff_parent')
    assert test_ref() is None


def test_linked_dictionary_error_handling():
    aa, bb = setup_tests()

    with nose.tools.assert_raises(KeyError):
        aa['no_such_key']

    with nose.tools.assert_raises(KeyError):
        del bb['no_such_key']

    with nose.tools.assert_raises(KeyError):
        bb['to_delete']

    with nose.tools.assert_raises(KeyError):
        del bb['to_delete']

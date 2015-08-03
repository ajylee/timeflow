import collections
import itertools
import weakref
import nose.tools


delete = ('delete', object)

class LinkedDictionary(collections.MutableMapping):
    def __init__(self, parent, base):
        self.parent = weakref.ref(parent) if parent is not None else lambda : None

        self.del_hooks = []

        if parent is not None:
            parent.diff_child = self.diff_parent = {}

            def del_hook():
                del self.diff_parent
            
            parent.del_hooks.append(del_hook)

        self.set_base(base)

    def set_base(self, base):
        if base is None:                     # None means to set base to self
            self.base = {}
            self.diff_base = {}
            self.diff_side = None
        elif base is self.parent():
            self.base = base
            self.diff_base = self.diff_parent
            self.diff_side = 1
        elif self.base is not None:  # is a child
            self.base = base
            self.diff_base = base.diff_parent
            self.diff_side = 0

    def __del__(self):
        # TODO: delete children's parent refs and diff_parent.
        #del self.parent.diff_child

        if self.parent():
            del self.diff_parent

        for del_hook in self.del_hooks:
            del_hook()

    def __setitem__(self, k, v):
        # cannot have children
        if self.parent():
            self.diff_parent[k] = (self.parent().get(k, delete), v)

        if self.diff_side is None:
            self.base[k] = v

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

    def __delitem__(self, k):
        # cannot have children
        if self.diff_side is None:
            try:
                del self.base[k]
            except KeyError:
                raise KeyError

        if self.parent():
            try:
                self.diff_parent[k] = (self.parent()[k], delete)
            except KeyError:
                # parent has no such key => key in self.diff_parent or KeyError
                try:
                    del self.diff_parent[k]
                except KeyError:
                    raise KeyError, 'no such key'


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


def test_linked_dictionary():
    class X(object):
        pass

    aa = LinkedDictionary(None, None)
    aa[1] = 10
    aa['to_delete'] = X()

    bb = LinkedDictionary(aa, aa)

    bb[1] = 20
    bb[2] = 30
    del bb['to_delete']

    with nose.tools.assert_raises(KeyError):
        del bb['no_such_key']

    assert aa[1] == 10
    assert bb[1] == 20
    assert 2 not in aa

    transfer_core(aa, bb)

    assert aa[1] == 10
    assert bb[1] == 20
    assert 2 not in aa

    assert hasattr(bb, 'diff_parent')
    test_ref = weakref.ref(aa['to_delete'])
    del aa
    assert not hasattr(bb, 'diff_parent')
    assert test_ref() is None


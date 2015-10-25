import weakref
import nose.tools

from timeflow.linked_structure import transfer_core
from timeflow.linked_set import LinkedSet


class X(object):
    pass


@nose.tools.nottest
def setup_tests():

    aa_egg = LinkedSet.first_egg(set())
    aa_egg.add(1)
    aa_egg.add('to_delete')

    x = X()
    aa_egg.add(x)

    aa = aa_egg.hatch()
    del aa_egg

    bb = aa.egg()

    bb.add(2)
    bb.remove('to_delete')
    bb.remove(x)

    return aa, bb

@nose.tools.nottest
def test_standard_assertions(aa, bb):
    assert 1 in aa
    assert 1 in bb

    assert 2 not in aa
    assert 2 in bb

    assert 'to_delete' in aa
    assert 'to_delete' not in bb

    assert 3 not in aa
    assert 3 not in bb


def test_basic():
    aa, bb = setup_tests()
    test_standard_assertions(aa, bb)


def test_transfer_core():
    aa, bb = setup_tests()
    transfer_core(aa, bb)

    test_standard_assertions(aa, bb)

    transfer_core(bb, aa)

    test_standard_assertions(aa, bb)


def test_memory_management():
    aa, bb = setup_tests()

    assert hasattr(bb, 'diff_parent')
    for elt in aa:
        if isinstance(elt, X):
            test_ref = weakref.ref(elt)
            del elt
            break
    del aa
    assert hasattr(bb, 'diff_parent')
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    assert not hasattr(bb, 'diff_parent')
    assert test_ref() is None

import weakref
import nose.tools

from timeflow.linked_structure import transfer_core
from timeflow.linked_set import first_egg


@nose.tools.nottest
def setup_tests():
    class X(object):
        pass

    aa_egg = first_egg({})
    aa_egg.add(1)
    aa_egg.add('to_delete')

    aa = aa_egg.hatch()
    del aa_egg

    bb = aa.egg()

    bb.add(2)
    bb.remove('to_delete')

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
    test_ref = weakref.ref(aa['to_delete'])
    del aa
    assert hasattr(bb, 'diff_parent')
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    assert not hasattr(bb, 'diff_parent')
    assert test_ref() is None

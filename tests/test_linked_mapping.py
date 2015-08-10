import weakref
import nose.tools

from timeflow.linked_structure import transfer_core
from timeflow.linked_mapping import first_egg


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

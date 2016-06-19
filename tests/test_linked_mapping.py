import weakref
import nose.tools

from timeflow.linked_structure import transfer_core
from timeflow.linked_mapping import LinkedMapping


@nose.tools.nottest
def setup_tests():

    aa_egg = LinkedMapping.first_egg({})
    aa_egg[1] = 10
    aa_egg['to_delete'] = 'to_delete_val'

    aa = aa_egg.hatch(); del aa_egg

    bb_egg = aa.egg()

    bb_egg[1] = 20
    bb_egg[2] = 30
    del bb_egg['to_delete']
    bb = bb_egg.hatch(); del bb_egg

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
    class X(object):
        pass

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['to_delete'] = X()

    aa = aa_egg.hatch(); del aa_egg
    bb_egg = aa.egg()

    del bb_egg['to_delete']
    bb = bb_egg.hatch(); del bb_egg

    bb.diff_parent is not None
    test_ref = weakref.ref(aa['to_delete'])
    del aa
    bb.diff_parent is not None
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    bb.diff_parent is None
    assert test_ref() is None


def test_linked_dictionary_error_handling():
    aa, bb = setup_tests()
    cc_egg = bb.egg()

    with nose.tools.assert_raises(KeyError):
        aa['no_such_key']


    with nose.tools.assert_raises(KeyError):
        bb['to_delete']

    with nose.tools.assert_raises(KeyError):
        bb['no_such_key']

    with nose.tools.assert_raises(TypeError):
        del bb['no_such_key']

    with nose.tools.assert_raises(TypeError):
        del bb['to_delete']


    with nose.tools.assert_raises(KeyError):
        del cc_egg['no_such_key']

    with nose.tools.assert_raises(KeyError):
        cc_egg['to_delete']

    with nose.tools.assert_raises(KeyError):
        del cc_egg['to_delete']

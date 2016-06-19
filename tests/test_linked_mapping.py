import weakref
import nose.tools

from timeflow.linked_structure import transfer_core, PARENT, CHILD, SELF, NO_VALUE
from timeflow.linked_mapping import LinkedMapping


@nose.tools.nottest
def setup_main_test_cases():

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['varies'] = 10
    aa_egg['to_delete'] = 'to_delete_val'

    aa = aa_egg.hatch(); del aa_egg

    bb_egg = aa.egg()

    bb_egg['varies'] = 20
    bb_egg['additional'] = 'additional_val'
    del bb_egg['to_delete']
    bb = bb_egg.hatch(); del bb_egg


    desired_aa = {'varies': 10,
                  'to_delete': 'to_delete_val'}

    desired_bb = {'varies': 20,
                  'additional': 'additional_val'}

    return aa, bb, desired_aa, desired_bb


def test_linked_dictionary():
    aa, bb, desired_aa, desired_bb = setup_main_test_cases()

    assert aa['varies'] == 10
    assert bb['varies'] == 20
    assert 'additional' not in aa

    assert aa == desired_aa
    assert bb == desired_bb, bb


def test_transfer_core():
    aa, bb, desired_aa, desired_bb = setup_main_test_cases()
    transfer_core(aa, bb)
    assert aa.relation_to_base == PARENT
    assert bb.relation_to_base == SELF

    assert aa == desired_aa
    assert bb == desired_bb

    transfer_core(bb, aa)
    assert aa.relation_to_base == SELF
    assert bb.relation_to_base == CHILD

    assert aa == desired_aa
    assert bb == desired_bb


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
    aa, bb, _unused_1, _unused_2 = setup_main_test_cases()
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


def test_diff():
    aa, bb, _unused_1, _unused_2 = setup_main_test_cases()

    assert bb.diff_parent == {'varies': (10, 20),
                              'to_delete': ('to_delete_val', NO_VALUE),
                              'additional': (NO_VALUE, 'additional_val')}

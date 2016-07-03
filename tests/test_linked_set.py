import weakref
import nose.tools

from timeflow.linked_structure import (transfer_core, create_core_in, hatch_egg_simple,
                                       CHILD, SELF, DIFF_LEFT, DIFF_RIGHT, diff)
from timeflow.linked_set import LinkedSet


class X(object):
    pass


@nose.tools.nottest
def setup_tests():

    aa_egg = LinkedSet.first_egg(set())
    aa_egg.add('always_here')
    aa_egg.add('to_delete')

    aa = hatch_egg_simple(aa_egg); del aa_egg

    bb_egg = aa.egg()

    bb_egg.add('added')
    bb_egg.remove('to_delete')
    bb = hatch_egg_simple(bb_egg); del bb_egg

    return aa, bb


@nose.tools.nottest
def test_standard_assertions(aa, bb):
    assert 'always_here' in aa
    assert 'always_here' in bb

    assert 'added' not in aa
    assert 'added' in bb

    assert 'to_delete' in aa
    assert 'to_delete' not in bb

    assert 'never_here' not in aa
    assert 'never_here' not in bb

    assert aa == {'always_here', 'to_delete'}, aa
    assert bb == {'always_here', 'added'}, bb


def test_basic():
    aa, bb = setup_tests()
    test_standard_assertions(aa, bb)


def test_transfer_core():
    aa, bb = setup_tests()
    transfer_core(aa, bb)

    test_standard_assertions(aa, bb)

    assert bb.relation_to_base == SELF

    transfer_core(bb, aa)

    test_standard_assertions(aa, bb)

    assert bb.relation_to_base == CHILD


def test_create_core_in():
    aa, bb = setup_tests()
    create_core_in(bb)

    test_standard_assertions(aa, bb)

    assert aa.relation_to_base == SELF
    assert bb.relation_to_base == SELF


def test_memory_management():
    aa_egg = LinkedSet.first_egg(set())

    x = X()
    aa_egg.add(x)

    aa = hatch_egg_simple(aa_egg); del aa_egg

    bb_egg = aa.egg()
    bb_egg.remove(x); del x

    bb = hatch_egg_simple(bb_egg); del bb_egg

    assert bb.diff_parent is not None
    for elt in aa:
        if isinstance(elt, X):
            test_ref = weakref.ref(elt)
            del elt
            break
    del aa
    assert bb.diff_parent is not None
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    assert bb.diff_parent is None
    assert test_ref() is None


def test_diff():
    aa, bb = setup_tests()

    assert dict(diff(aa, bb)) == {'to_delete': DIFF_LEFT,
                                  'added': DIFF_RIGHT}

    assert dict(diff(bb, aa)) == {'to_delete': DIFF_RIGHT,
                                  'added': DIFF_LEFT}


    assert list(diff(aa, aa)) == []

    cc = LinkedSet.first_egg({'always_here', 'to_delete', 'new_val'}).hatch()

    assert (dict(diff(bb, cc))
            == dict(LinkedSet._diff(bb, cc))
            == {'to_delete': DIFF_RIGHT,
                'added': DIFF_LEFT,
                'new_val': DIFF_RIGHT})

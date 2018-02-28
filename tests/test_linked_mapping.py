import weakref
import pytest
import logging

from timeflow.linked_structure import (transfer_core, create_core_in,
                                       hatch_egg_simple, hatch_egg_optimized,
                                       PARENT, CHILD, SELF, NO_VALUE, diff)
from timeflow.linked_mapping import LinkedMapping


logger = logging.getLogger(__name__)

def ghosted(rr: weakref.ReferenceType):
    '''Whether the referred object has been deleted or has no referrers'''
    import gc

    return rr() is None or not gc.get_referrers(rr())


@pytest.mark.skip(reason='not a test')
def setup_main_test_cases():

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['varies'] = 10
    aa_egg['constant'] = 100
    aa_egg['to_delete'] = 'to_delete_val'

    aa = hatch_egg_simple(aa_egg); del aa_egg

    bb_egg = aa.egg()

    bb_egg['varies'] = 20
    bb_egg['additional'] = 'additional_val'
    del bb_egg['to_delete']
    bb = hatch_egg_simple(bb_egg); del bb_egg


    desired_aa = {'varies': 10,
                  'constant': 100,
                  'to_delete': 'to_delete_val'}

    desired_bb = {'varies': 20,
                  'constant': 100,
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


def test_create_core_in():
    aa, bb, desired_aa, desired_bb = setup_main_test_cases()
    create_core_in(bb)
    assert aa.relation_to_base == SELF
    assert bb.relation_to_base == SELF

    assert aa == desired_aa
    assert bb == desired_bb


def test_memory_management(log_level):
    import timeflow.linked_structure

    logger.setLevel(log_level)
    timeflow.linked_structure.logger.setLevel(log_level)

    class X(object):
        pass

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['to_delete'] = X()
    aa_egg['to_keep'] = X()

    aa = hatch_egg_simple(aa_egg); del aa_egg
    aa.debug_label = 'aa'
    bb_egg = aa.egg()

    del bb_egg['to_delete']
    bb = hatch_egg_simple(bb_egg); del bb_egg
    bb.debug_label = 'bb'

    bb.diff_parent is not None
    test_ref = weakref.ref(aa['to_delete'])
    logger.debug('del aa')
    del aa
    bb.diff_parent is not None
    assert test_ref() is not None

    transfer_core(bb.parent(), bb)    # bb.parent() points to aa until core is transferred

    assert bb.diff_parent is None
    assert test_ref() is None


def test_hatch_empty_mapping():
    class X(object):
        pass

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['to_delete'] = X()

    aa = hatch_egg_simple(aa_egg); del aa_egg
    bb_egg = aa.egg()

    del bb_egg['to_delete']
    assert not bb_egg

    bb = hatch_egg_optimized(bb_egg); del bb_egg
    assert not bb
    assert bb.relation_to_base == SELF

    test_ref = weakref.ref(aa['to_delete'])
    del aa
    assert test_ref() is None


def test_linked_dictionary_error_handling():
    aa, bb, _unused_1, _unused_2 = setup_main_test_cases()
    cc_egg = bb.egg()

    with pytest.raises(KeyError):
        aa['no_such_key']


    with pytest.raises(KeyError):
        bb['to_delete']

    with pytest.raises(KeyError):
        bb['no_such_key']

    with pytest.raises(TypeError):
        del bb['no_such_key']

    with pytest.raises(TypeError):
        del bb['to_delete']


    with pytest.raises(KeyError):
        del cc_egg['no_such_key']

    with pytest.raises(KeyError):
        cc_egg['to_delete']

    with pytest.raises(KeyError):
        del cc_egg['to_delete']


def test_diff():
    aa, bb, _unused_1, _unused_2 = setup_main_test_cases()

    assert dict(diff(aa, bb)) == {'varies': (10, 20),
                                  'to_delete': ('to_delete_val', NO_VALUE),
                                  'additional': (NO_VALUE, 'additional_val')}, dict(diff(aa, bb))


    assert dict(diff(bb, aa)) == {k: (v[1], v[0]) for k,v in diff(aa, bb)}


    assert list(diff(aa, aa)) == []


    cc = LinkedMapping.first_egg({'varies': 'new_varies_val',
                                  'constant': 100,
                                  'new_cc_key': 'new_cc_val'}).hatch()

    assert (dict(diff(bb, cc))
            == dict(LinkedMapping._diff(bb, cc))
            == {'varies': (20, 'new_varies_val'),
                'additional': ('additional_val', NO_VALUE),
                'new_cc_key': (NO_VALUE, 'new_cc_val')}), (dict(diff(bb,cc)),
                                                           dict(diff(bb,cc)) == dict(LinkedMapping.diff(bb, cc)))


def hatch_egg_optimized_with_debug_messages(egg, debug_label_suffix):
    orig_parent_relation_to_base = egg.parent().relation_to_base
    orig_parent_base = (egg.parent().debug_label
                        if egg.parent().relation_to_base is SELF
                        else egg.parent().base.debug_label)

    ss = hatch_egg_optimized(egg); del egg
    ss.debug_label = ss.parent().debug_label + debug_label_suffix

    if (ss.relation_to_base is SELF
        and orig_parent_relation_to_base is SELF
        and ss.parent().relation_to_base is PARENT
        and ss.parent().unproxied_base is ss):
        logger.debug('Transferred core %s -> %s', ss.parent().debug_label, ss.debug_label)
    elif (ss.parent().unproxied_base is not ss):
        logger.debug(
            'Created a fork, orig_parent_relation_to_base: {}, parent: {}, hatched: {}, orig_parent_base: {}, parent.base: {}'
            .format(
                {CHILD:'CHILD', PARENT:'PARENT', SELF:'SELF'}[orig_parent_relation_to_base],
                ss.parent().debug_label,
                ss.debug_label,
                orig_parent_base,
                (ss.parent().debug_label
                 if ss.parent().relation_to_base is SELF
                 else ss.parent().base.debug_label),
            ))
    else:
        logger.debug('??')

    return ss


def test_hatch_egg_optimized(log_level: int):
    # Create a fork with no strong refs, then reference through a weak ref. Test if there is a ReferenceError.
    # (There shouldn't be.)

    import timeflow.linked_structure

    logger.setLevel(log_level)
    timeflow.linked_structure.logger.setLevel(log_level)

    aa_egg = LinkedMapping.first_egg({})
    aa_egg['varies'] = ('a', 0)
    aa_egg['constant'] = 100

    aa = hatch_egg_optimized(aa_egg); del aa_egg
    aa.debug_label = 'aa'

    for ii in range(5):
        logger.debug('top: aa.base: %s', (aa.debug_label if aa.relation_to_base is SELF else aa.base.debug_label))

        #~~ start bb ~~#
        logger.debug('start bb{}'.format(ii))

        bb_egg = aa.egg()
        bb_egg['varies'] = ('b', ii)
        bb = hatch_egg_optimized_with_debug_messages(bb_egg, debug_label_suffix='.bb{}'.format(ii)); del bb_egg

        #~~ start cc ~~#

        logger.debug('start cc{}'.format(ii))
        cc_egg = aa.egg()
        cc_egg['varies'] = ('c', ii)

        # this should create a fork
        cc = hatch_egg_optimized_with_debug_messages(cc_egg, debug_label_suffix='.cc{}'.format(ii)); del cc_egg

        assert aa.unproxied_base is bb   # tests whether fork was created
        assert aa.relation_to_base is PARENT and isinstance(aa.base, weakref.ProxyType)

        bb_ref = weakref.ref(bb)
        logger.debug('del bb{}'.format(ii))
        del bb

        assert ghosted(bb_ref)

        # this may trigger ReferenceError
        logger.debug('assert aa.base is {}'.format(cc.debug_label))
        assert aa.unproxied_base is cc
        assert aa.base == {'constant': 100, 'varies': ('c', ii)}

        assert cc.parent() is aa
        assert isinstance(aa.base, weakref.ProxyType)

        logger.debug('del cc{}'.format(ii))
        cc_ref = weakref.ref(cc)
        del cc

        assert ghosted(cc_ref)

        logger.debug('bottom: aa.base: %s', (aa.debug_label if aa.relation_to_base is SELF else aa.base.debug_label))

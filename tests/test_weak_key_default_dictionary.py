import collections

import timeflow.util.collections as tuc
import timeflow

class Weakable(object):
    pass


def test_weak_key_default_dictionary_1():
    wkd = tuc.WeakKeyDefaultDictionary(set)

    def _inner():
        w = Weakable()

        wkd[w].add(10)

        assert wkd[w] == set([10])

    _inner()

    assert wkd.items() == []


def test_weak_value_default_dictionary():

    strong_refs = []

    def _mk_referenced_set():
        _s = set()
        strong_refs.append(_s)
        return _s
        

    wvd = tuc.WeakValueDefaultDictionary(_mk_referenced_set)

    wvd[1].add(10)

    assert wvd[1] == set([10])

    del strong_refs[:]

    assert wvd.items() == []


def test_clean():
    wkd = tuc.WeakKeyDefaultDictionary(set)
    w = Weakable()

    wkd[w].add(10)

    wkd[w].remove(10)

    assert w in wkd

    tuc.clean_if_empty(wkd, w)

    assert w not in wkd


def test_clean_if_empty_and_isolated():
    timeline = timeflow.StepLine()
    dd = collections.defaultdict(lambda : timeflow.BridgeMappingFlow(timeline))

    plan = timeline.new_plan()
    dd[1].at(plan)[0] = 10
    timeline.commit(plan); del plan

    tuc.clean_if_empty_and_isolated(dd, timeline.HEAD, 1)

    assert 1 in dd

    plan = timeline.new_plan()
    del dd[1].at(plan)[0]
    timeline.commit(plan); del plan

    assert 1 in dd

    tuc.clean_if_empty_and_isolated(dd, timeline.HEAD, 1)

    assert 1 not in dd


test_weak_key_default_dictionary_1()
test_clean()
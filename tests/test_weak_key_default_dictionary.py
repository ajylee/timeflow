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

    assert list(wkd.items()) == []


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

    assert list(wvd.items()) == []


def test_clean():
    wkd = tuc.WeakKeyDefaultDictionary(set)
    w = Weakable()

    wkd[w].add(10)

    wkd[w].remove(10)

    assert w in wkd

    tuc.clean_if_empty(wkd, w)

    assert w not in wkd

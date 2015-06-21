from timefunc.td_mapping import StepMapping, BasedDictionary, _reroot_base, BasedMapping
from timefunc.base import TimeLine, now
from collections import OrderedDict

def test_td_mapping():
    now_copy = dict(a=10, b=20)
    dd = StepMapping(now_copy)

    dd.future['a'] = 30
    dd.future['b'] = 2 * dd.future['a']

    future_copy = dict(a=30, b=60)

    assert dict(dd.now) == now_copy
    assert dict(dd.future) == future_copy


def test_td_mapping_2():
    now_copy = dict(a=10, b=20)
    tl = TimeLine({0: BasedMapping(now_copy.copy())})
    future = BasedDictionary(tl[now])

    future['a'] = 30
    future['b'] = 2 * future['a']

    tl.advance(1, future)

    future_copy = dict(a=30, b=60)

    assert dict(tl[0]) == now_copy
    assert dict(tl[1]) == future_copy
    assert tl[1]._base == tl[0]

    _reroot_base(tl[0], tl[1])

    assert dict(tl[0]) == now_copy
    assert dict(tl[1]) == future_copy
    assert tl[0]._base == tl[1]

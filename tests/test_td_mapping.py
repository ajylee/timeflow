from timefunc.td_mapping import StepDictionary, BasedDictionary, BasedMapping
from timefunc.base import TimeLine, now
from collections import OrderedDict

def test_td_mapping_2():
    now_copy = dict(a=10, b=20)
    tl = TimeLine({0: BasedMapping(now_copy.copy())})
    future = BasedDictionary(tl[now])

    future['a'] = 30
    future['b'] = 2 * future['a']

    tl.advance(1, future)

    future_copy = dict(a=30, b=60)

    assert tl[0] == now_copy
    assert tl[1] == future_copy
    assert tl[1]._base == tl[0]

    tl[0]._reroot_base(tl[1])

    assert tl[0] == now_copy
    assert tl[1] == future_copy
    assert tl[0]._base == tl[1]


def test_step_dictionary():
    original = dict(a=10, b=20)
    sd = StepDictionary(original.copy(), copy=False)

    sd.stage['a'] = 30
    sd.stage['c'] = 100

    assert sd.now == original
    sd.commit()
    assert sd.now == {'a':30, 'b':20, 'c':100}

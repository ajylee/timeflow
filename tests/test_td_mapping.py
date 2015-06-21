from timefunc import StepMapping, DerivedDictionary, DerivedMapping, TDMapping
from timefunc import TimeLine, now
from collections import OrderedDict

class TestData:
    original = dict(a=10, b=20, to_delete=1000)


def test_td_mapping_2():
    original = TestData.original
    tl = TDMapping({0: DerivedMapping(original.copy())})
    stage = tl.new_stage()

    stage['a'] = 30
    stage['b'] = 2 * stage['a']
    del stage['to_delete']

    assert stage._base == tl[0]
    assert tl[0] == original

    tl.commit(1, stage)

    assert tl[0] == original
    assert tl[1] == dict(a=30, b=60)
    assert tl[0]._base == tl[1]


def test_step_mapping():
    original = TestData.original
    sd = StepMapping(original.copy())

    sd.stage['a'] = 30
    sd.stage['new'] = 100
    del sd.stage['to_delete']

    assert sd.head == original
    sd.commit()
    assert sd.head == {'a':30, 'b':20, 'new':100}


def test_step_mapping_errors():
    pass

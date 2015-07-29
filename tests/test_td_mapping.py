from timeflow import StepMapping, DerivedDictionary, SnapshotMapping, Plan, StepPlan
from timeflow import TimeLine, now
from collections import OrderedDict
import nose.tools

class TestData:
    original = dict(a=10, b=20, to_delete=1000)


def test_td_mapping_2():
    original = TestData.original
    tl = TimeLine({0: SnapshotMapping(original)})

    plan = Plan([tl], 0)

    tl.at(plan)['a'] = 30
    tl.at(plan)['b'] = 2 * plan[tl]['a']
    del tl.at(plan)['to_delete']

    assert tl.at(plan)._base == tl.at(0)
    assert tl.at(0) == original

    plan.commit(1)

    assert tl.at(0) == original
    assert tl.at(1) == dict(a=30, b=60)
    assert tl.at(0)._base == tl.at(1)

    assert tl.at(0)['a'] == 10


def test_step_mapping():
    original = TestData.original
    sm = StepMapping(original.copy())

    plan = StepPlan([sm])

    sm.at(plan)['a'] = 30
    sm.at(plan)['new'] = 100
    del sm.at(plan)['to_delete']

    assert sm.head == original
    plan.commit()
    assert sm.head == {'a':30, 'b':20, 'new':100}


def test_step_mapping_errors():
    original = TestData.original
    sm = StepMapping(original.copy())

    with nose.tools.assert_raises(TypeError):
        sm.head['x'] = 10

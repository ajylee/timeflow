from timeflow import StepSet, DerivedSet, Plan, StepPlan
from timeflow import TimeLine, now
from collections import OrderedDict
import nose.tools

class TestData:
    original = {10, 20, 1000, 'to_delete'}


def test_td_set():
    original = TestData.original
    tl = TimeLine({0: DerivedSet(original.copy(), None, None)})

    plan = Plan([tl], 0)

    plan[tl].add(30)
    plan[tl].remove('to_delete')

    assert plan[tl]._base == tl[0]
    assert tl[0] == original

    plan.commit(1)

    assert tl[0] == original
    assert tl[1] == {10, 20, 30, 1000}
    assert tl[0]._base == tl[1]


def test_step_set():
    original = TestData.original
    ss = StepSet(original.copy())

    plan = StepPlan([ss])

    plan[ss].add(30)
    plan[ss].add(100)
    plan[ss].remove('to_delete')

    assert ss.head == original
    plan.commit()
    assert ss.head == {10, 20, 30, 100, 1000}

    plan[ss].add(40)
    plan[ss].remove(10)
    assert ss.head == {10, 20, 30, 100, 1000}
    plan.commit()
    assert ss.head == {20, 30, 40, 100, 1000}


def test_step_mapping_errors():
    original = TestData.original
    sm = StepSet(original.copy())

    with nose.tools.assert_raises(AttributeError):
        sm.head.add(30)

    with nose.tools.assert_raises(AttributeError):
        sm.head.remove('to_delete')

from timeflow import Plan, StepLine, SetFlow, BridgeSetFlow
from timeflow import TimeLine, now
from collections import OrderedDict
import nose.tools

class TestData:
    original = {10, 20, 1000, 'to_delete'}


def test_td_set():
    original = TestData.original
    tl = TimeLine()

    initial_plan = tl.new_plan()
    sf = SetFlow()
    sf.at(initial_plan).update(original)

    e0 = tl.commit(initial_plan)

    plan = tl.new_plan()

    sf.at(plan).add(30)
    sf.at(plan).remove('to_delete')

    assert sf.at(e0) == original

    e1 = tl.commit(plan)

    assert sf.at(e0) == original
    assert sf.at(e1) == {10, 20, 30, 1000}


def test_step_line():
    tl = StepLine()

    initial = tl.new_plan()
    sf = SetFlow()
    sf.at(initial).update(TestData.original)

    tl.commit(initial); del initial

    plan = tl.new_plan()

    sf.at(plan).add(30)
    sf.at(plan).add(100)
    sf.at(plan).remove('to_delete')

    assert sf.at(tl.HEAD) == TestData.original
    tl.commit(plan); del plan
    assert sf.at(tl.HEAD) == {10, 20, 30, 100, 1000}

    plan2 = tl.new_plan()

    sf.at(plan2).add(40)
    sf.at(plan2).remove(10)
    assert sf.at(tl.HEAD) == {10, 20, 30, 100, 1000}
    tl.commit(plan2); del plan2
    assert sf.at(tl.HEAD) == {20, 30, 40, 100, 1000}


def test_empty_set():
    tl = TimeLine()
    original = TestData.original

    initial = tl.new_plan([])
    sm = SetFlow.introduce_at(initial, set())
    tl.commit(initial)
    del initial

    plan = tl.new_plan()
    sm.at(plan).add(30)
    sm.at(plan).add(100)
    tl.commit(plan); del plan

    plan = tl.new_plan()
    sm.at(plan).remove(30)
    sm.at(plan).remove(100)
    tl.commit(plan); del plan

    assert set(sm.at(tl.HEAD)) == set()


def test_bridge_set():
    tl = TimeLine()
    plan = tl.new_plan()

    sf = BridgeSetFlow(tl, TestData.original)

    sf.at(plan).add(30)
    assert 30 not in sf

    tl.commit(plan)
    assert 30 in sf


def test_bridge_set_errors():
    tl = TimeLine()
    sf = BridgeSetFlow(tl, TestData.original)

    with nose.tools.assert_raises(AttributeError):
        sf.head.add(30)

    with nose.tools.assert_raises(AttributeError):
        sf.head.remove('to_delete')

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


def test_step_set():
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


def test_step_mapping_errors():
    tl = TimeLine()
    sf = BridgeSetFlow(tl, TestData.original)

    with nose.tools.assert_raises(AttributeError):
        sf.head.add(30)

    with nose.tools.assert_raises(AttributeError):
        sf.head.remove('to_delete')

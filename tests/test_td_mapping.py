from timeflow import Plan, BridgeMappingFlow
from timeflow import TimeLine, StepLine, Event

import weakref
from collections import OrderedDict
from timeflow.td_mapping import MappingFlow
import nose.tools


class TestData:
    original = dict(a=10, b=20, to_delete=1000)


def test_td_mapping_2():
    tl = TimeLine()

    original = TestData.original

    initial_plan = tl.new_plan([])

    flow = tdi = MappingFlow.introduce_at(initial_plan, original)

    e0 = tl.commit(initial_plan)

    plan = tl.new_plan([tdi])

    tdi.at(plan)['a'] = 30
    tdi.at(plan)['b'] = 2 * tdi.at(plan)['a']
    del tdi.at(plan)['to_delete']


    assert tdi.at(e0) == original

    e1 = tl.commit(plan)

    assert tdi.at(e0) == original
    assert tdi.at(e1) == dict(a=30, b=60)

    assert tdi.at(e0)['a'] == 10


def test_step_line():
    tl = StepLine()
    original = TestData.original

    initial = tl.new_plan([])
    sm = MappingFlow.introduce_at(initial, original)
    tl.commit(initial)

    plan = tl.new_plan()

    sm.at(plan)['a'] = 30
    sm.at(plan)['new'] = 100
    del sm.at(plan)['to_delete']

    test_refs = [weakref.ref(tl.HEAD),
                 weakref.ref(sm.at(tl.HEAD))]

    assert sm.at(tl.HEAD) == original

    tl.commit(plan)
    del plan

    assert all(test_ref() is None for test_ref in test_refs)
    assert sm.at(tl.HEAD) == {'a':30, 'b':20, 'new':100}


def test_empty_mapping():
    tl = TimeLine()
    original = TestData.original

    initial = tl.new_plan([])
    sm = MappingFlow.introduce_at(initial, {})
    tl.commit(initial)
    del initial

    plan = tl.new_plan()
    sm.at(plan)['a'] = 30
    sm.at(plan)['new'] = 100
    tl.commit(plan); del plan

    plan = tl.new_plan()
    del sm.at(plan)['a']
    del sm.at(plan)['new']
    tl.commit(plan); del plan

    assert dict(sm.at(tl.HEAD)) == {}



def test_bridge_mapping_errors():
    tl = StepLine()

    sm = BridgeMappingFlow(tl)
    plan = tl.new_plan()
    sm.at(plan).update(TestData.original)

    with nose.tools.assert_raises(TypeError):
        sm['a'] = 10

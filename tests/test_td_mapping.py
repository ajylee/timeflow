from timeflow import SnapshotMapping, Plan, BridgeMappingFlow
from timeflow import TimeLine, StepLine, now, Event

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

    flow = tdi = MappingFlow()
    flow.at(initial_plan).update(original)

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


def test_step_mapping():
    tl = StepLine()
    original = TestData.original

    sm = MappingFlow()
    initial = tl.new_plan([])
    sm.at(initial).update(original)
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


def test_bridge_mapping_errors():
    tl = StepLine()

    sm = BridgeMappingFlow(tl, TestData.original.copy())

    with nose.tools.assert_raises(TypeError):
        sm['a'] = 10

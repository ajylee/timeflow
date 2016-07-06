from timeflow import Plan, MappingFlow
from timeflow import TimeLine, StepLine, Event

import weakref
from collections import OrderedDict
import nose.tools


def setup_first_timeline():
    tl = TimeLine()

    initial_plan = tl.new_plan()
    mflow = MappingFlow.introduce_at(initial_plan, {'a':'a0', 'b':'b0'})
    tl.commit(initial_plan)

    _updates = [
        {mflow: {'a': 'a1'}},
        {mflow: {'a': 'a2'}},
        {mflow: {'a': 'a_3 branch_0'}},]

    for elt in _updates:
        _plan = tl.new_plan()

        mflow_update = elt[mflow]
        if mflow_update:
            mflow.at(_plan).update(mflow_update)

        tl.commit(_plan)

    return tl, mflow


def test_fork_1():
    tl, mflow = setup_first_timeline()

    # Make Fork
    tl_2 = TimeLine(tl.HEAD.parent)
    plan = tl_2.new_plan()
    mflow.at(plan)['a'] = 'a_3 branch_1'
    tl_2.commit(plan)

    tl_head = weakref.ref(tl.HEAD)
    wr_tl = weakref.ref(tl)
    del tl

    #print gc.get_referrers(wr_tl())
    #print gc.get_referrers(tl_head())

    import inspect, gc
    del tl_2

    #aa = gc.get_referrers(tl_head())
    #print gc.get_referrers(aa[0])

    assert wr_tl() is None or gc.get_referrers(wr_tl()) == []
    assert tl_head() is None or gc.get_referrers(tl_head()) == [],  (gc.get_referrers(tl_head()))

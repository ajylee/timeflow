from timeflow import StepMapping, DerivedDictionary, SnapshotMapping, Plan, StepPlan
from timeflow import TimeLine, StepLine, now, Event
from collections import OrderedDict
from timeflow.td_mapping import MappingFlow
import nose.tools

class Repo(object):

    def new_root_event(self):
        assert not self.refs['HEAD'] or self.refs[self.current_branch]
        _e = Event(parent=None)
        self.refs[self.current_branch] = _e
        self.refs['HEAD'] = _e
        return _e


class StepRepo(Repo):
    """Repo that only keeps the current version"""

    def commit(self, plan):
        event = Repo.commit(self, plan)
        # TODO: forget previous events
        return event


class TestData:
    original = dict(a=10, b=20, to_delete=1000)


def test_td_mapping_2():
    tl = TimeLine()

    original = TestData.original

    initial_plan = tl.new_plan([])

    flow = tdi = MappingFlow(tl.instance)
    flow.at(initial_plan).update(original)

    e0 = initial_plan.commit()

    plan = tl.new_plan([tdi])

    tdi.at(plan)['a'] = 30
    tdi.at(plan)['b'] = 2 * tdi.at(plan)['a']
    del tdi.at(plan)['to_delete']


    assert tdi.at(plan)._base == tdi.at(e0)
    assert tdi.at(e0) == original

    e1 = tl.commit(plan)

    assert tdi.at(e0) == original
    assert tdi.at(e1) == dict(a=30, b=60)
    assert tdi.at(e0)._base == tdi.at(e1)

    assert tdi.at(e0)['a'] == 10


def test_step_mapping():
    tl = TimeLine()
    original = TestData.original

    sm = MappingFlow(tl.instance)
    initial = tl.new_plan([])
    sm.at(initial).update(original)
    initial.commit()

    plan = tl.new_plan()

    sm.at(plan)['a'] = 30
    sm.at(plan)['new'] = 100
    del sm.at(plan)['to_delete']

    assert sm.at(tl.HEAD) == original
    tl.commit(plan)
    tl.HEAD.forget_parent()
    assert sm.at(tl.HEAD) == {'a':30, 'b':20, 'new':100}


def nottest_step_mapping_errors():
    repo = Repo()

    original = TestData.original

    e0 = repo.new_root_event()
    sm = StepMapping({e0: SnapshotMapping(original.copy())})

    with nose.tools.assert_raises(TypeError):
        sm.at(repo.HEAD)['a'] = 10

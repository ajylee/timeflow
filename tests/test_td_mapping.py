from timeflow import StepMapping, DerivedDictionary, SnapshotMapping, Plan, StepPlan
from timeflow import TimeLine, now, Event
from collections import OrderedDict
import nose.tools

class Repo(object):
    def __init__(self):
        self.current_branch = 'master'
        self.refs = {'HEAD': None,
                  self.current_branch: None}

    @property
    def HEAD(self):
        return self.refs['HEAD']

    def new_root_event(self):
        assert not self.refs['HEAD'] or self.refs[self.current_branch]
        _e = Event(parent=None)
        self.refs[self.current_branch] = _e
        self.refs['HEAD'] = _e
        return _e

    def commit(self, plan):
        event = Event(parent=plan.base_time)
        plan.commit(event)
        self.refs[self.current_branch] = event
        self.refs['HEAD'] = event
        return event

    def new_plan(self, timelines):
        base_event = self.HEAD
        return Plan(timelines, base_event)


class TestData:
    original = dict(a=10, b=20, to_delete=1000)


def test_td_mapping_2():
    repo = Repo()

    original = TestData.original

    e0 = repo.new_root_event()
    tl = TimeLine({e0: SnapshotMapping(original)})

    plan = repo.new_plan([tl])

    tl.at(plan)['a'] = 30
    tl.at(plan)['b'] = 2 * tl.at(plan)['a']
    del tl.at(plan)['to_delete']

    assert tl.at(plan)._base == tl.at(e0)
    assert tl.at(e0) == original

    e1 = repo.commit(plan)

    assert tl.at(e0) == original
    assert tl.at(e1) == dict(a=30, b=60)
    assert tl.at(e0)._base == tl.at(e1)

    assert tl.at(e0)['a'] == 10


def test_step_mapping():
    repo = Repo()
    original = TestData.original

    e0 = repo.new_root_event()
    sm = StepMapping({e0: SnapshotMapping(original.copy())})

    plan = repo.new_plan([sm])

    sm.at(plan)['a'] = 30
    sm.at(plan)['new'] = 100
    del sm.at(plan)['to_delete']

    assert sm.at(repo.HEAD) == original
    repo.commit(plan)
    assert sm.at(repo.HEAD) == {'a':30, 'b':20, 'new':100}


def test_step_mapping_errors():
    repo = Repo()

    original = TestData.original

    e0 = repo.new_root_event()
    sm = StepMapping({e0: SnapshotMapping(original.copy())})

    with nose.tools.assert_raises(TypeError):
        sm.at(repo.HEAD)['a'] = 10

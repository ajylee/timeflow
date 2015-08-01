import collections
import uuid
import bisect
from abc import abstractmethod
import weakref
from event import index_bounds, Event


now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))


class Plan(object):
    def __init__(self, timeline, flows, base_event):
        self.timeline = timeline
        self.base_event = base_event

        self.stage = {timeline: timeline.instance[flow, base_event].new_stage()
                   for flow in flows}

        self.categories = collections.defaultdict(set)

        self.frozen = set()    # a set of frozen timeline ids

    def __getitem__(self, flow):
        try:
            return self.stage[flow]
        except KeyError:
            _stage = self.timeline.instance[flow, self.base_event].new_stage()
            self[flow] = _stage
            return _stage

    def __setitem__(self, timeline, small_stage):
        assert timeline not in self.frozen, 'Tried to set frozen timeline'
        self.stage[timeline] = small_stage

    def __contains__(self, timeline):
        return timeline in self.stage

    def update(self, other_plan):
        for timeline, _other_stage in other_plan.stage.items():
            if timeline in self:
                self[timeline].update(_other_stage)
            else:
                self[timeline] = _other_stage

    def commit(self):
        return self.timeline.commit(self)

    def introduce(self, snapshot_or_stage):
        flow = TDItem(self.timeline.instance)
        self[flow] = snapshot_or_stage
        return flow


class SubPlan(Plan):
    def __init__(self, super_plan, category_key, readable_category_keys):
        self.category_key = category_key
        self.category = super_plan.categories[self.category_key]
        self.super_plan = super_plan
        self.stage = super_plan.stage
        self.readable = reduce(set.union,
                            (super_plan.categories[_key]
                             for _key in readable_category_keys))

    def __setitem__(self, timeline, small_stage):
        self.super_plan[timeline] = small_stage
        self.category_set.add(timeline)

    def __contains__(self, timeline):
        return timeline in self.category

    def __getitem__(self, timeline):
        if timeline not in self and timeline not in self.readable:
            if timeline not in self.super_plan:
                return timeline.at_time(self.super_plan.base_event)
            else:
                raise KeyError, 'Access denied to timeline {}'.format(timeline)
        else:
            return self.super_plan.stage[timeline]

    def freeze(self):
        """Freeze all timelines in the subplan"""
        self.super_plan.frozen.update(self.category)


class StepPlan(Plan):
    def __init__(self, step_objs):
        Plan.__init__(self, step_objs, now)


class TDItem(object):
    def __init__(self, instance):
        self.instance = instance

    def __hash__(self):
        return object.__hash__(self)

    def at(self, plan_or_event):
        if isinstance(plan_or_event, Plan):
            return plan_or_event[self]
        else:
            return self.at_event(plan_or_event)

    def at_event(self, event):
        return self.instance[self, event]

    def read_at(self, plan_or_time):
        if isinstance(plan_or_time, Plan):
            if self in plan_or_time:
                return plan_or_time[self]
            else:
                return self.at(plan_or_time.base_event)
        else:
            return self.at(plan_or_time)


class TimeLine(object):
    def __init__(self):
        self.mapping = {}
        self.events = []
        self.current_branch = 'master'
        self.refs = {'HEAD': None,
                  self.current_branch: None}
        self.event_map = {}
        self.flow_map = {}
        self.instance = {}

    @property
    def HEAD(self):
        return self.refs['HEAD']

    def new_plan(self, timelines):
        base_event = self.HEAD
        return Plan(self, timelines, base_event)

    def commit(self, plan):
        """For timelines with the head as the root. That means the latest value in the
        timeline is a standalone mapping, and all others are derived from it.

        """
        event = Event(parent=plan.base_event)
        parent_event = event._parent()

        for td_item, stage in plan.stage.items():
            frozen_item = stage.frozen_view()
            self.instance[td_item, event] = frozen_item

            if (td_item, parent_event) in self.instance:
                self.instance[td_item, parent_event]._reroot_base(frozen_item)

        self.refs['HEAD'] = self.refs[self.current_branch] = event
        return event

    def forget(self, time):
        del self.instance[time]
        index = bisect.bisect_left(time)
        del self.mod_times[index]

    def forget_range(self, time_range, inclusive=True):
        left_bound, right_bound = index_bounds(self.events, time_range, inclusive)
        to_remove = self.events[left_bound:right_bound]
        for time in to_remove:
            del self.instance[time]
        del self.events[left_bound:right_bound]


class DerivedObject(object):
    @abstractmethod
    def _reroot_base(self, new_root):
        """For efficiency only. Results of all public API calls must remain
        invariant, but private variables may mutate.

        """
        pass

    @abstractmethod
    def new_stage(self):
        pass


class DerivedStage(object):
    @abstractmethod
    def frozen_view(self):
        pass

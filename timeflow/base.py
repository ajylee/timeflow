import collections
import uuid
import bisect
from abc import abstractmethod
import weakref
from event import index_bounds, Event


now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))


class Plan(object):
    def __init__(self, timelines, base_time):
        self.base_time = base_time

        self.stage = {timeline: timeline.at_time(base_time).new_stage()
                   for timeline in timelines}

        self.categories = collections.defaultdict(set)

        self.frozen = set()    # a set of frozen timeline ids

    def __getitem__(self, timeline):
        try:
            return self.stage[timeline]
        except KeyError:
            _stage = timeline.at_time(self.base_time).new_stage()
            self[timeline] = _stage
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
        self.timeline.commit(self)


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
                return timeline.at_time(self.super_plan.base_time)
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
    def __hash__(self):
        return object.__hash__(self)

    def at(self, plan_or_event):
        if isinstance(plan_or_event, Plan):
            return plan_or_event[self]
        else:
            return self.at_event(plan_or_event)

    def at_time(self, time):
        return self.event_mapping[time]

    def read_at(self, plan_or_time):
        if isinstance(plan_or_time, Plan):
            if self in plan_or_time:
                return plan_or_time[self]
            else:
                return self.at(plan_or_time.base_time)
        else:
            return self.at(plan_or_time)


class TimeLine(object):
    def __init__(self, mapping):
        self.mapping = mapping
        self.events = sorted(event for td_item, event in mapping)
        self.current_branch = 'master'
        self.refs = {'HEAD': None,
                  self.current_branch: None}
        self.event_map = {}
        self.flow_map = {}

    @property
    def HEAD(self):
        return self.refs['HEAD']

    def new_plan(self, timelines):
        base_event = self.HEAD
        return Plan(timelines, base_event)

    def commit(self, plan):
        """For timelines with the head as the root. That means the latest value in the
        timeline is a standalone mapping, and all others are derived from it.

        """
        event = Event(parent=plan.base_time)
        parent_event = event.parent()

        for td_item, stage in plan.stage.items():
            frozen_item = stage.frozen_view()
            self.event_mapping[td_item, event] = frozen_item

            if parent_event is not None:
                self.event_mapping[td_item, parent_event]._reroot_base(frozen_item)

    def forget(self, time):
        del self.event_mapping[time]
        index = bisect.bisect_left(time)
        del self.mod_times[index]

    def forget_range(self, time_range, inclusive=True):
        left_bound, right_bound = index_bounds(self.events, time_range, inclusive)
        to_remove = self.events[left_bound:right_bound]
        for time in to_remove:
            del self.event_mapping[time]
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

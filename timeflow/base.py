import collections
import uuid
from abc import abstractmethod
from event import Event, NullEvent


now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))


class Plan(object):
    modified_flow = 'modified_flow'
    new_flow = 'new_flow'

    def __init__(self,  base_event, only_flows=None):
        self.only_flows = only_flows   # unimplemented; restricts modifications

        self.base_event = base_event

        self.stage = {}

        self.categories = collections.defaultdict(set)

        self.frozen = set()    # a set of frozen flows

    def get_flow(self, flow):
        try:
            return self.stage[flow]
        except KeyError:
            _stage = self.base_event.instance.get(flow, flow.default).new_stage()
            self[flow] = _stage
            return _stage

    def __setitem__(self, flow, instance):
        assert flow not in self.frozen, 'Tried to set frozen flow'
        self.stage[flow] = instance

    def __contains__(self, flow):
        return flow in self.stage

    def update(self, other_plan):
        for flow, _other_stage in other_plan.stage.items():
            if flow in self:
                self[flow].update(_other_stage)
            else:
                self[flow] = _other_stage

    def introduce(self, flow, snapshot_or_stage):
        self[flow] = (snapshot_or_stage, self.new_flow)
        self.new_flows.append(flow)
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


class TimeLine(object):
    def __init__(self):
        self.HEAD = NullEvent

    @property
    def instance(self):
        return self.HEAD.instance

    def new_plan(self, only_flows=None):
        base_event = self.HEAD
        return Plan(base_event, only_flows)

    def commit(self, plan):
        """For timelines with the head as the root. That means the latest value in the
        timeline is a standalone mapping, and all others are derived from it.

        """
        parent_event = plan.base_event
        event = Event(parent=parent_event)

        for flow, instance in plan.stage.items():
            frozen_item = instance.frozen_view()
            event.instance[flow] = frozen_item

            if frozen_item is not flow.default:
                _parent_item = parent_event.instance.get(flow, flow.default)
                _parent_item._reroot_base(frozen_item)

        self.HEAD = event
        return event


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()


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

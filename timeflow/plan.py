import collections
from functools import partial
import weakref
import logging

from .linked_structure import SELF, CHILD
from .event import Event
from .flow import Flow

logger = logging.getLogger(__name__)


class Plan(object):
    modified_flow = 'modified_flow'
    new_flow = 'new_flow'

    # statuses
    planning = 'planning'
    committed = 'committed'
    committing = 'committing'
    cancelled = 'cancelled'

    def __init__(self,  base_event: Event, only_flows=None):
        self.only_flows = only_flows   # unimplemented; restricts modifications

        self.base_event = base_event

        self.stage = {}

        self.categories = collections.defaultdict(partial(SubPlan, weakref.proxy(self)))

        self.frozen = set()    # a set of frozen flows

        self.status = self.planning

    def get_flow_instance(self, flow: Flow):
        try:
            return self.stage[flow]
        except KeyError:
            _stage = self.base_event.get_flow_instance(flow).egg()
            self.stage[flow] = _stage
            return _stage

    def read_flow_instance(self, flow: Flow):
        try:
            return self.stage[flow]
        except KeyError:
            return self.base_event.read_flow_instance(flow)

    #def __setitem__(self, flow, instance):
    #    assert flow not in self.frozen, 'Tried to set frozen flow'
    #    self.stage[flow] = instance

    def set_flow_instance(self, flow: Flow, value):
        self.stage[flow] = value

    def __getitem__(self, key):
        return self.categories[key]

    def __contains__(self, flow: Flow):
        return flow in self.stage

    def update(self, other_plan):
        for flow, _other_stage in other_plan.stage.items():
            if flow in self.stage:
                self.stage[flow].update(_other_stage)
            else:
                self.stage[flow] = _other_stage

    def hatch(self):
        """Create a new event from the plan

        WARNING: Assumes flow instances of the parent event have "cores".

        """

        parent_instance_map = self.base_event.instance
        instance_map = parent_instance_map.egg()

        for flow, instance in self.stage.items():
            try:
                hatched_item = instance.hatch()
            except AttributeError:
                instance_map[flow] = instance
                continue

            if hatched_item is flow.default:
                instance_map.pop(flow, None)
            else:
                instance_map[flow] = hatched_item
                if instance_map[flow] is not hatched_item:
                    logger.warn('Plan.hatch: redundant attempt to update flow')

        return Event(instance_map=instance_map.hatch(),
                     parent=self.base_event)


class SubPlan(object):
    def __init__(self, parent_proxy):
        self._parent = parent_proxy   # weakref proxy to super plan
        self._keys = set()

    def __contains__(self, flow):
        return flow in self._keys

    def get_flow_instance(self, flow):
        self._keys.add(flow)
        return self._parent.get_flow_instance(flow)

    def read_flow_instance(self, flow):
        if flow in self._keys:
            return self._parent.read_flow_instance(flow)
        else:
            raise KeyError

    def set_flow_instance(self, flow, value):
        self._keys.add(flow)
        self._parent.set_flow_instance(flow, value)

    def update(self, other_plan):
        try:
            self._keys.update(other_plan._keys)
        except KeyError:
            self._keys.update(other_plan.stage)

        self._parent.update(other_plan)


class OldSubPlan(Plan):
    def __init__(self, super_plan, category_key, readable_category_keys):
        self.category_key = category_key
        self.category = super_plan.categories[self.category_key]
        self.super_plan = super_plan
        self.stage = super_plan.stage
        self.readable = set.union(* (super_plan.categories[_key]
                                  for _key in readable_category_keys))

    def __setitem__(self, timeline, small_stage):
        self.super_plan[timeline] = small_stage
        self.category_set.add(timeline)

    def __contains__(self, timeline):
        return timeline in self.category

    def __getitem__(self, timeline):
        if timeline not in self.category and timeline not in self.readable:
            if timeline not in self.super_plan:
                return timeline.at_time(self.super_plan.base_event)
            else:
                raise KeyError('Access denied to timeline {}'.format(timeline))
        else:
            return self.super_plan.stage[timeline]

    def freeze(self):
        """Freeze all timelines in the subplan"""
        self.super_plan.frozen.update(self.category)

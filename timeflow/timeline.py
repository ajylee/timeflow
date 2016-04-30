import collections
import uuid
from abc import abstractmethod
from .event import Event, NullEvent
from linked_structure import transfer_core, SELF
from .plan import Plan

now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))

class TimeLine(object):
    def __init__(self):
        self.HEAD = NullEvent

    #@property
    #def instance(self):
    #    return self.HEAD.instance

    def new_plan(self, only_flows=None):
        base_event = self.HEAD
        return Plan(base_event, only_flows)

    def commit(self, plan):
        """For timelines with the head as the root. That means the latest value in the
        timeline is a standalone mapping, and all others are derived from it.

        """
        parent_event = plan.base_event
        instance_map = parent_event.instance.copy()

        for flow, instance in plan.stage.items():
            frozen_item = instance.hatch()
            instance_map[flow] = frozen_item

            if frozen_item is not flow.default and frozen_item.relation_to_base is not SELF:
                _parent_item = parent_event.instance.get(flow, flow.default)
                transfer_core(_parent_item, frozen_item)

        self.HEAD = Event(parent=parent_event, instance_map=instance_map)
        return self.HEAD


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()


import collections
import uuid
from abc import abstractmethod
from .event import Event, NullEvent
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
        self.HEAD = plan.hatch()
        return self.HEAD


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()

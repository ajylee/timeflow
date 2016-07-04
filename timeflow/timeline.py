import collections
import uuid
from abc import abstractmethod
from .event import Event, NullEvent, _drop_from_tuple
from .plan import Plan

now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))

class TimeLine(object):
    def __init__(self, HEAD=None):
        self.HEAD = HEAD if HEAD is not None else NullEvent()
        self.HEAD.referrers += (self,)

    #@property
    #def instance(self):
    #    return self.HEAD.instance

    def new_plan(self, only_flows=None):
        base_event = self.HEAD
        return Plan(base_event, only_flows)

    def commit(self, plan):
        base_event = plan.base_event
        assert base_event == self.HEAD
        self.HEAD = plan.hatch()

        base_event.referrers = _drop_from_tuple(base_event.referrers, self)
        self.HEAD.referrers += (self,)

        return self.HEAD


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()

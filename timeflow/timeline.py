import collections
import uuid
import operator
import weakref
from abc import abstractmethod

import toolz

from .event import Event, NullEvent, _drop_from_tuple, walk_to_fork
from .plan import Plan
from .linked_structure import (LinkedStructure, transfer_core, walk_to_core,
                               SELF, PARENT, CHILD)

now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))

def referent_linked_structures(event):
    for _elt in toolz.cons(event.instance, event.instance.itervalues()):
        try:
            yield _elt
        except AttributeError:
            pass


class TimeLine(object):

    def __init__(self, HEAD=None, require_single_plan=True):
        self.HEAD = HEAD if HEAD is not None else NullEvent()
        self.ref = weakref.ref(self)
        self.HEAD.referrers += (self.ref,)
        self.require_single_plan = require_single_plan

        # Set to True when `new_plan` is called, set to False when `commit` is called
        self.has_uncommitted_plan = False

    #@property
    #def instance(self):
    #    return self.HEAD.instance

    def new_plan(self, only_flows=None):
        if self.require_single_plan:
            assert not self.has_uncommitted_plan, '{} tried to start new plan while having an uncommitted plan.'.format(self)

        self.has_uncommitted_plan = True

        base_event = self.HEAD
        return Plan(base_event, only_flows)

    def commit(self, plan: Plan):
        if self.require_single_plan:
            assert self.has_uncommitted_plan, '{} tried to commit a plan, but there should be no uncommitted plan.'.format(self)
        assert plan.status == Plan.planning
        plan.status = Plan.committing

        base_event = plan.base_event
        assert base_event == self.HEAD
        self.HEAD = plan.hatch()

        base_event.referrers = _drop_from_tuple(base_event.referrers, self.ref)
        self.HEAD.referrers += (self.ref,)

        self.has_uncommitted_plan = False
        plan.status = Plan.committed
        return self.HEAD

    def cancel(self, plan: Plan):
        if self.require_single_plan:
            assert self.has_uncommitted_plan, '{} tried to cancel a plan, but there should be no uncommitted plan.'.format(self)

        plan.status = Plan.cancelled
        self.has_uncommitted_plan = False

    def __del__(self):
        """Update Event.referrers, LinkedStructure.base, alt_bases"""
        self.HEAD.referrers = _drop_from_tuple(self.HEAD.referrers, self.ref)
        _event = self.HEAD
        path_to_fork, has_fork = walk_to_fork(self.HEAD)

        for _event, _parent in toolz.sliding_window(2, path_to_fork):
            _parent.referrers = _drop_from_tuple(_parent.referrers, _event)

        if has_fork and all(isinstance(_referrer, TimeLine)
                            for _referrer in path_to_fork[-1].referrers):
            # covers case where there is no fork topology; i.e. a branch has
            # been started but no fork commit has been made.
            fork = path_to_fork[-1]
            for _elt in non_independent_linked_structures(fork):
                if (_elt.relation_to_base == PARENT
                    and type(_elt.base) is not weakref.ProxyType):
                    _parent.base = weakref.proxy(_parent.base)

        #if has_fork:
        #    fork = path_to_fork[-1]
        #    del path_to_fork

        #    for maybe_linked_structure in toolz.cons(fork.instance,
        #                                             fork.instance.itervalues()):
        #        if isinstance(maybe_linked_structure, LinkedStructure):
        #            ls = maybe_linked_structure


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()

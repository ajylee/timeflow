import collections
import uuid
import operator
from abc import abstractmethod

import toolz

from .event import Event, NullEvent, _drop_from_tuple, in_live_event
from .plan import Plan
from .linked_structure import walk_to_core, SELF, PARENT, CHILD

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

    def __del__(self):
        """Update Event.referrers, LinkedStructure.base, alt_bases"""
        self.HEAD.referrers = _drop_from_tuple(self.HEAD.referrers, self)
        _event = self.HEAD
        path_to_fork, has_fork = walk_to_fork(self.HEAD)

        for _event, _parent in toolz.sliding_window(2, path_to_fork):
            _parent.referrers = _drop_from_tuple(_parent.referrers, _event)

        if has_fork:
            fork = path_to_fork[-1]
            del path_to_fork

            for maybe_linked_structure in toolz.cons(fork.instance,
                                                     fork.instance.itervalues()):
                if isinstance(maybe_linked_structure, LinkedStructure):
                    _update_base_and_alt_bases(maybe_linked_structure)


def _update_base_and_alt_bases(linked_structure_):
    to_keep = list(filter(in_live_event, linked_structure_.alt_bases))

    if (linked_structure_.relation_to_base == SELF or
        in_live_event(linked_structure_.base)):
        linked_structure_.alt_bases = to_keep or None

    elif to_keep:
            if linked_structure_.base.parent() is linked_structure_:
                relation_to_base = PARENT
            elif linked_structure_.parent() is linked_structure_.base:
                relation_to_base = CHILD
            else:
                raise ValueError, "invalid relation_to_base"
            linked_structure_.set_base(to_keep[0], relation_to_base)
            linked_structure_.alt_bases = to_keep[1:] or None
    else:
        linked_structure_.alt_bases = None
        _path = walk_to_core(linked_structure_)
        _path.reverse()  # now _path is from core to linked_structure_
        for ls1, ls2 in toolz.sliding_window(2, _path):
            transfer_core(ls1, ls2)


class StepLine(TimeLine):
    def commit(self, plan):
        TimeLine.commit(self, plan)
        self.HEAD.forget_parent()

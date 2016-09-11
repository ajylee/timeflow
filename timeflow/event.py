import time as _time
import bisect
import weakref
from . import linked_mapping
from .ref_tools import strong_ref, empty_ref



def representative_event(events, event):
    """If event is not in the list of events, return the event recorded just before."""
    index = bisect.bisect_right(events, event)
    if index == 0:
        raise ValueError("requested time too early in timeline")
    else:
        return events[index - 1]


def index_bounds(sorted_list, bounds, inclusive=True):
    if inclusive:
        left_bound = bisect.bisect_left(sorted_list, bounds[0])
        right_bound = bisect.bisect_right(sorted_list, bounds[1])
    else:
        left_bound = bisect.bisect_right(sorted_list, bounds[0])
        right_bound = bisect.bisect_left(sorted_list, bounds[1])

    return left_bound, right_bound


# Infinity
# ########

class _NegativeInfinity:
    @staticmethod
    def __cmp__(other):
        return -1

    def __neg__(self):
        return inf

    def __repr__(self):
        return 'NegativeInfinity'

class _Infinity:
    @staticmethod
    def __cmp__(other):
        return 1

    def __neg__(self):
        return _neg_inf

    def __repr__(self):
        return 'Infinity'

inf = _Infinity()
_neg_inf = _NegativeInfinity()


def _drop_from_tuple(tt, element):
    if len(tt) == 1:
        return ()
    else:
        return tuple(elt for elt in tt if elt is not element)


# #########

class NullEvent:
    instance = linked_mapping.empty_linked_mapping
    time = -inf
    count = 0
    parent = None

    def __init__(self):
        self.referrers = ()

    @staticmethod
    def get_flow_instance(flow):
        return flow.default

    read_flow_instance = get_flow_instance


class Event(object):
    def __init__(self, instance_map, parent):
        """Events in a timeline map flows to instances

        :param linked_mapping.LinkedMapping instance_map:
            maps flows to instances.

        :param Event parent:
            will be weak referenced, for walking event graph.

        """
        self.parent = parent
        parent.referrers += (self,)

        self.instance = instance_map

        self.referrers = ()
        self.time = int(_time.time())

        if parent and parent.time == self.time:
            self.count = parent.count + 1
        else:
            self.count = 0

    def get_flow_instance(self, flow):
        return self.instance.get(flow, flow.default)

    read_flow_instance = get_flow_instance

    def __hash__(self):
        return hash((self.time, self.count))

    def __repr__(self):
        return 'Event(time={self.time}, count={self.count}, id={id})'.format(
            self=self, id=hex(id(self)))

    @property
    def time_order(self):
        return (self.time, self.count)

    def forget_parent(self):
        _parent = self.parent
        _parent.referrers = _drop_from_tuple(_parent.referrers, self)
        self.parent = None


def walk_to_fork(event):
    path = [event]
    while len(path[-1].referrers) < 2:
        if path[-1].parent:
            path.append(path[-1].parent)
        else:
            return path, False

    return path, True


def walk(self, steps=1):
    target = self
    nn = abs(steps)

    while nn > 0:
        nn = nn - 1

        if steps > 0:
            try:
                target = target.referrers[0]
            except IndexError:
                raise ValueError('No child')

        else:
            target = target.parent

            if target is None:
                return NullEvent

    return target

import time as _time
import bisect
import weakref
import linked_mapping
from ref_tools import strong_ref, empty_ref



def representative_event(events, event):
    """If event is not in the list of events, return the event recorded just before."""
    index = bisect.bisect_right(events, event)
    if index == 0:
        raise ValueError, "requested time too early in timeline"
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



# #########

class NullEvent:
    instance = linked_mapping.empty_linked_mapping
    time = -inf
    count = 0

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
        self.parent = strong_ref(parent) if parent else empty_ref
        if parent:
            parent.child = weakref.ref(self)

        self.instance = instance_map

        self.child = empty_ref
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

    def __cmp__(self, other):
        return cmp((self.time, self.count), (other.time, other.count))

    def __repr__(self):
        return 'Event(time={self.time}, count={self.count})'.format(self=self)

    def forget_parent(self):
        self.parent = empty_ref


def walk(self, steps=1):
    target = self
    nn = abs(steps)

    while nn > 0:
        nn = nn - 1

        if steps > 0:
            target = target.child()
            if target is None:
                raise ValueError, 'No child'

        else:
            target = target.parent()

            if target is None:
                return NullEvent

    return target

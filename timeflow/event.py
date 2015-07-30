import time as _time
import bisect
import weakref

def empty_ref():
    return None

class Event(object):
    def __init__(self, parent=None):
        self._parent = weakref.ref(parent) if parent else empty_ref
        if parent:
            parent._child = weakref.ref(self)

        self._child = empty_ref
        self.time = _time.time()

        if parent and parent.time == self.time:
            self.count = parent.count + 1
        else:
            self.count = 0

    def __hash__(self):
        return hash((self.time, self.count))

    def __cmp__(self, other):
        return cmp((self.time, self.count), (other.time, other.count))

    def parent(self, nn=1):
        target = self
        while nn > 0:
            nn = nn - 1
            target = target._parent()
            if not target:
                raise ValueError, 'No parent'

        return target

    def child(self, nn=1):
        target = self
        while nn > 0:
            nn = nn - 1
            target = target._child()
            if not target:
                raise ValueError, 'No child'

        return target

    def new_child(self):
        return Event(parent=self)

    def __repr__(self):
        return 'Event(time={self.time}, count={self.count})'.format(self=self)


def representative_event(events, event):
    """If event is not in the list of events, return the event recorded just before."""
    index = bisect.bisect_right(events, event)
    if index == 0:
        raise ValueError, "requested time too early in timeline"
    else:
        return events[index - 1]

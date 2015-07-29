import time as _time
import logging
from timeflow.event import Event

logging.basicConfig()
logger = logging.getLogger(__name__)


def test_child():
    e0 = Event()
    e1 = e0.new_child()
    e2 = e1.new_child()

    assert e0.child(1) == e1
    assert e0.child(2) == e2

    assert e2.parent(1) == e1
    assert e2.parent(2) == e0

    assert e0 < e1 < e2


def test_event_time_collision():
    parent_event = Event()

    count = 0

    start_time = parent_event.time

    while count < 2:
        event = parent_event.new_child()

        if event.count == 0 and parent_event.count > 1:
            #print parent_event
            count = count + 1

        assert event > parent_event

        parent_event = event

        if event.time - start_time > 5:
            raise ValueError, 'Aborting test; use a faster setup.'

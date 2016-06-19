"""
Using SetFlow, tests behavior that is common to all Flows
"""

from timeflow import Plan, StepLine, SetFlow, BridgeSetFlow
from timeflow import TimeLine, now
from collections import OrderedDict
import nose.tools

class TestData:
    original = {10, 20, 1000, 'to_delete'}


def test_read_at():
    original = TestData.original
    tl = TimeLine()

    initial_plan = tl.new_plan()
    sf = SetFlow()
    sf2 = SetFlow()  # Test behavior when not set in initial plan

    sf.at(initial_plan).update(original)

    e0 = tl.commit(initial_plan)

    assert sf2.read_at(e0) == set()

    plan = tl.new_plan()

    sf.at(plan).add(30)
    sf.at(plan).remove('to_delete')

    # `read_at` should not generate instance egg if it doesn't exist; `at` should.
    assert sf2.read_at(plan) is not sf2.at(plan)
    assert sf2.read_at(plan) is sf2.at(plan)
    sf2.at(plan).add(40)

    assert sf.read_at(e0) == original
    assert sf.read_at(e0) is sf.at(e0)

    e1 = tl.commit(plan)

    assert sf.read_at(e0) == original
    assert sf.read_at(e1) == {10, 20, 30, 1000}

    assert sf2.read_at(e1) == {40}

    plan2 = tl.new_plan()

    # sf2.read_at(plan2) should not have the `add` attribute.
    with nose.tools.assert_raises(AttributeError):
        sf2.read_at(plan2).add(10)

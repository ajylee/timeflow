from timefunc import StepSet, DerivedSet
from timefunc import TimeLine, now
from collections import OrderedDict
import nose.tools

class TestData:
    original = {10, 20, 1000, 'to_delete'}


def test_td_set():
    original = TestData.original
    tl = TimeLine({0: DerivedSet(original.copy(), None, None)})
    stage = tl.new_stage()

    stage.add(30)
    stage.remove('to_delete')

    assert stage._base == tl[0]
    assert tl[0] == original

    tl.commit(1, stage)

    assert tl[0] == original
    assert tl[1] == {10, 20, 30, 1000}
    assert tl[0]._base == tl[1]


def test_step_set():
    original = TestData.original
    ss = StepSet(original.copy())

    ss.stage.add(30)
    ss.stage.add(100)
    ss.stage.remove('to_delete')

    assert ss.head == original
    ss.commit()
    assert ss.head == {10, 20, 30, 100, 1000}

    ss.stage.add(40)
    ss.stage.remove(10)
    assert ss.head == {10, 20, 30, 100, 1000}
    ss.commit()
    assert ss.head == {20, 30, 40, 100, 1000}


def test_step_mapping_errors():
    original = TestData.original
    sm = StepSet(original.copy())

    with nose.tools.assert_raises(AttributeError):
        sm.head.add(30)
        
    with nose.tools.assert_raises(AttributeError):
        sm.head.remove('to_delete')

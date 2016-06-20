from timeflow import Plan, StepLine, Flow, TimeLine
from timeflow.flow import SimpleFlow


class IntFlow(SimpleFlow):
    default = 0


def test_int_flow():
    tl = TimeLine()

    initial_plan = tl.new_plan()
    si = IntFlow.introduce_at(initial_plan, 1)
    si2 = IntFlow()

    assert si2.read_at(initial_plan) == 0

    e0 = tl.commit(initial_plan)
    assert si2.read_at(e0) == 0

    plan = tl.new_plan()

    si.set_at(plan, 2)

    assert si.read_at(e0) == 1

    e1 = tl.commit(plan)

    assert si.read_at(e0) == 1
    assert si.read_at(e1) == 2

from timefunc.td_mapping import StepMapping

def test_td_mapping():
    now_copy = dict(a=10, b=20)
    dd = StepMapping(now_copy)

    dd.future['a'] = 30
    dd.future['b'] = 2 * dd.future['a']

    future_copy = dict(a=30, b=60)
    
    assert dict(dd.now) == now_copy
    assert dict(dd.future) == future_copy

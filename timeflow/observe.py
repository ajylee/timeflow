
class TDObserver(object):
    def __init__(self, rule, *observed_args, **observed_kwargs):
        self.rule = rule
        self.observed_args = observed_args
        self.observed_kwargs = observed_kwargs

    def __getitem__(self, time):
        return rule(*[oa[time] for oa in observed_args],
                    **{k:v[time] for k,v in observed_kwargs.iteritems()})


def TDRule(rule):
    # convenience
    return tz.partial(TDObserver, rule)

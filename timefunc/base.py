import collections
import toolz as tz

class TimeLine(collections.Mapping):
    def __init__(self, time_mapping=None):
        if time_mapping is not None:
            self.time_mapping = time_mapping
            self.latest_time = max(time_mapping)
        else:
            self.time_mapping = {}
            self.latest_time = None

    def __getitem__(self, time):
        return self.time_mapping[time]

    def __len__(self):
        return len(self.time_mapping)

    def __iter__(self):
        return iter(self.time_mapping)

    def advance(self, time, future):
        self.time_mapping[time] = plan
        assert (self.latest_time is None) or (time > self.latest_time)
        self.latest_time = time

    @property
    def latest(self):
        if self.latest_time is not None:
            return self.time_mapping[self.latest_time]
        else:
            return None


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


class BasedObject(object):
    def __init__(self, base, actual):
        self._base = _base
        if self._base != actual:
            self._actual = actual
        else:
            self._actual = no_change

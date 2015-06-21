import collections
import toolz as tz
import uuid
import bisect

now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))


def index_bounds(sorted_list, bounds, inclusive=True):
    if inclusive:
        left_bound = bisect.bisect_left(bounds[0])
        right_bound = bisect.bisect_right(bounds[1])
    else:
        left_bound = bisect.bisect_right(bounds[0])
        right_bound = bisect.bisect_left(bounds[1])

    return left_bound, right_bound


class TimeLine(collections.Mapping):
    def __init__(self, time_mapping):
        self.time_mapping = time_mapping
        self.mod_times = sorted(self.time_mapping)
        if not self.mod_times:
            raise ValueError, "time_mapping cannot be empty"

    def __getitem__(self, time):
        if time is now:
            return self.time_mapping[self.mod_times[-1]]
        else:
            try:
                return self.time_mapping[time]
            except KeyError:
                index = bisect.bisect_right(self.mod_times, time)
                if index == 0:
                    raise ValueError, "requested time too early in timeline"
                else:
                    return self.time_mapping[self.mod_times[index - 1]]

    def __len__(self):
        return len(self.time_mapping)

    def __iter__(self):
        return iter(self.time_mapping)

    def advance(self, time, future):
        assert (time > self.mod_times[-1])
        self.mod_times.append(time)
        self.time_mapping[time] = future

    def forget(self, time):
        del self.time_mapping[time]
        index = bisect.bisect_left(time)
        del self.mod_times[index]

    def forget_range(self, time_range, inclusive=True):
        left_bound, right_bound = index_bounds(self.mod_times, time_range, inclusive)
        to_remove = self.mod_times[left_bound:right_bound]
        for time in to_remove:
            del self.time_mapping[time]
        del self.mod_times[left_bound:right_bound]


class RootedTimeLine(TimeLine):
    # override
    def advance(self, time, future):
        orig_latest_time = self.mod_times[-1]
        TimeLine.advance(self, time, future)
        new_latest_time = time
        self.time_mapping[orig_latest_time]._reroot_base(self.time_mapping[new_latest_time])


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

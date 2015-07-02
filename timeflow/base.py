import collections
import toolz as tz
import uuid
import bisect
from abc import abstractmethod


now = ('now', uuid.UUID('5e625fb4-7574-4720-bb91-3a598d2332bd'))


_id_count = -1

def new_timeflow_id():
    global _id_count
    _id_count += 1
    return _id_count


class Plan(object):
    def __init__(self, timelines, base_time):
        self._count = 0
        self.base_time = base_time

        self.stage = {
            id(timeline): (timeline, timeline[base_time].new_stage())
            for timeline in timelines}

    def _gen_id(self):
        self._count += 1
        return self._count

    def __getitem__(self, timeline):
        try:
            return self.stage[id(timeline)][1]
        except KeyError:
            _stage = timeline[self.base_time].new_stage()
            self[timeline] = _stage
            return _stage

    def __setitem__(self, timeline, small_stage):
        self.stage[id(timeline)] = (timeline, small_stage)

    def __contains__(self, timeline):
        return id(timeline) in self.stage

    def update(self, other_plan):
        for timeline, _other_stage in other_plan.stage.values():
            if timeline in self:
                self[timeline].update(_other_stage)
            else:
                self[timeline] = _other_stage

    def commit(self):
        for timeline, stage in self.stage.values():
            timeline.commit(self.base_time, stage)


class StepPlan(Plan):
    def __init__(self, step_objs):
        self.base_time = now
        self.stage = {
            id(step_obj): (step_obj, step_obj.new_stage())
            for step_obj in step_objs}

    def __getitem__(self, step_obj):
        try:
            return self.stage[id(step_obj)][1]
        except KeyError:
            _stage = step_obj.head.new_stage()
            self[step_obj] = _stage
            return _stage

    def commit(self):
        for step_obj, stage in self.stage.values():
            step_obj.commit(stage)


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
        self._timeflow_id = new_timeflow_id()

    @property
    def head(self):
        return self.time_mapping[self.mod_times[-1]]

    def at(self, plan_or_time):
        if isinstance(plan_or_time, Plan):
            return plan_or_time[self]
        else:
            return self[plan_or_time]

    def commit(self, time, stage):
        """For timelines with the head as the root. That means the latest value in the
        timeline is a standalone mapping, and all others are derived from it.

        """
        orig_latest_time = self.mod_times[-1]
        new_latest_time = time
        assert new_latest_time > orig_latest_time
        self.mod_times.append(new_latest_time)
        self.time_mapping[new_latest_time] = stage.frozen_view()
        self.time_mapping[orig_latest_time]._reroot_base(self.time_mapping[new_latest_time])

    def __getitem__(self, time):
        if time is now:
            return self.head
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


class DerivedObject(object):
    @abstractmethod
    def _reroot_base(self, new_root):
        """For efficiency only. Results of all public API calls must remain
        invariant, but private variables may mutate.

        """
        pass

    @abstractmethod
    def new_stage(self):
        pass


class DerivedStage(object):
    @abstractmethod
    def frozen_view(self):
        pass

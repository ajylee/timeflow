import collections
from .linked_structure import transfer_core, SELF


class Plan(object):
    modified_flow = 'modified_flow'
    new_flow = 'new_flow'

    def __init__(self,  base_event, only_flows=None):
        self.only_flows = only_flows   # unimplemented; restricts modifications

        self.base_event = base_event

        self.stage = {}

        self.categories = collections.defaultdict(set)

        self.frozen = set()    # a set of frozen flows

    def get_flow_instance(self, flow):
        try:
            return self.stage[flow]
        except KeyError:
            _stage = self.base_event.instance.get(flow, flow.default).egg()
            self.stage[flow] = _stage
            return _stage

    #def __setitem__(self, flow, instance):
    #    assert flow not in self.frozen, 'Tried to set frozen flow'
    #    self.stage[flow] = instance

    def __contains__(self, flow):
        return flow in self.stage

    def update(self, other_plan):
        for flow, _other_stage in other_plan.stage.items():
            if flow in self.stage:
                self[flow].update(_other_stage)
            else:
                self[flow] = _other_stage


class SubPlan(Plan):
    def __init__(self, super_plan, category_key, readable_category_keys):
        self.category_key = category_key
        self.category = super_plan.categories[self.category_key]
        self.super_plan = super_plan
        self.stage = super_plan.stage
        self.readable = reduce(set.union,
                            (super_plan.categories[_key]
                             for _key in readable_category_keys))

    def __setitem__(self, timeline, small_stage):
        self.super_plan[timeline] = small_stage
        self.category_set.add(timeline)

    def __contains__(self, timeline):
        return timeline in self.category

    def __getitem__(self, timeline):
        if timeline not in self.category and timeline not in self.readable:
            if timeline not in self.super_plan:
                return timeline.at_time(self.super_plan.base_event)
            else:
                raise KeyError, 'Access denied to timeline {}'.format(timeline)
        else:
            return self.super_plan.stage[timeline]

    def freeze(self):
        """Freeze all timelines in the subplan"""
        self.super_plan.frozen.update(self.category)

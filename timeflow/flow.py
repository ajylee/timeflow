
class Flow(object):
    default = 'need override'

    @classmethod
    def introduce_at(cls, plan, snapshot_or_stage):
        _flow = cls()
        _flow.at(plan).update(snapshot_or_stage)
        return _flow

    def __hash__(self):
        return object.__hash__(self)

    def at(self, event_like):
        return event_like.get_flow_instance(self)

    def read_at(self, event_like):
        return event_like.read_flow_instance(self)


class SimpleFlow(Flow):
    default = None

    @classmethod
    def introduce_at(cls, plan, value):
        _flow = cls()
        _flow.set_at(plan, value)
        return _flow

    def set_at(self, plan, value):
        plan.stage[self] = value

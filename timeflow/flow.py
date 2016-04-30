
class Flow(object):
    default = 'need override'

    def __hash__(self):
        return object.__hash__(self)

    def at(self, event_like):
        return event_like.get_flow_instance(self)

    def read_at(self, event_like):
        pass

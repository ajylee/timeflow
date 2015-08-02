
class Flow(object):
    def __init__(self, instance):
        self.instance = instance

    def __hash__(self):
        return object.__hash__(self)

    def at(self, event_like):
        return event_like.get_flow(self)

    def read_at(self, event_like):
        pass

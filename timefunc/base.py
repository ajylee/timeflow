
class TDObject(object):
    def __init__(self, time_mapping):
        self.time_mapping = time_mapping
        self.now = max(time_mapping)

        self.next_future_time = None
        self.next_future = None

    def __getitem__(self, time):
        return self.time_mapping[time]

    def advance(self):
        self.now = 
    

class Observed(object):
    def __init__(self, observed):
        self.observed = observed

    def __getitem__(self, time):
        return observed[time] = 

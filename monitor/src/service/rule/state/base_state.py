class State(object):
    def __init__(self):
        pass

    def current_state(self):
        return str(self)

    def on_event(self, event):
        pass

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.__class__.__name__

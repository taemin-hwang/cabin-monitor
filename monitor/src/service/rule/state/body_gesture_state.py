from service.rule.state.base_state import State

class IdleState(State):
    def on_event(self, event):
        if event == 'up':
            return UpState()
        elif event == 'down':
            return DownState()
        elif event == 'left':
            return LeftState()
        elif event == 'right':
            return RightState()
        elif event == 'raise_left_hand':
            return RaiseLeftHandState()
        elif event == 'raise_right_hand':
            return RaiseRightHandState()
        elif event == 'making_O':
            return MakingOState()
        elif event == 'making_X':
            return MakingXState()
        elif event == 'invalid':
            return InvalidState()
        else:
            return self

class InvalidState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class UpState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class DownState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class LeftState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class RightState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class RaiseRightHandState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class RaiseLeftHandState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class MakingXState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self

class MakingOState(State):
    def on_event(self, event):
        if event == 'idle':
            return IdleState()
        else:
            return self


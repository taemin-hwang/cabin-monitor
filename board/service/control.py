import math

from enum import Enum

class ControlStatus(Enum):
    IDLE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    INVALID = 5

class Control:
    def __init__(self):
        self._current_status = ControlStatus.INVALID
        self._previous_status = ControlStatus.INVALID
        self._idle_elbow = [0, 0]
        self._idle_wrist = [0, 0]

    def get_control(self, keypoints):
        self.update_status(keypoints)
        if self._current_status != self._previous_status:
            self._previous_status = self._current_status
        else:
            return ControlStatus.INVALID.value
        return self._current_status.value

    def get_distance(self, point1, point2):
        return math.sqrt(((point1[0]-point2[0])**2)+((point1[1]-point2[1])**2))

    def update_status(self, keypoints):
        right_elbow = keypoints[7]
        right_wrist = keypoints[9]
        shoulder_distance = self.get_distance(keypoints[6], keypoints[5])

        if right_wrist[2] < 0.3 or right_elbow[2] < 0.3:
            self._current_status = ControlStatus.INVALID
            return
        if keypoints[5][2] < 0.3 or keypoints[6][2] < 0.3:
            self._current_status = ControlStatus.INVALID
            return

        # if self._current_status == ControlStatus.INVALID:
        elbow_to_wrist_dist = self.get_distance(right_elbow, right_wrist)
        elbow_to_wrist_ratio = elbow_to_wrist_dist / shoulder_distance

        if (elbow_to_wrist_ratio < 0.5):
            self._current_status = ControlStatus.IDLE
            self._idle_elbow = [right_elbow[0], right_elbow[1]]
            self._idle_wrist = [right_wrist[0], right_wrist[1]]

        elif self._current_status == ControlStatus.IDLE:
            elbow_to_idle_elbow_dist = self.get_distance(right_elbow, self._idle_elbow)
            elbow_to_idle_elbow_ratio = elbow_to_idle_elbow_dist / shoulder_distance
            if elbow_to_idle_elbow_ratio > 0.5:
                self._current_status = ControlStatus.INVALID
            else:
                elbow_to_wrist_dist = self.get_distance(right_elbow, right_wrist)
                elbow_to_wrist_ratio = elbow_to_wrist_dist / shoulder_distance
                if elbow_to_wrist_ratio > 0.5:
                    elbow_x = right_elbow[0]
                    elbow_y = right_elbow[1]
                    wrist_x = right_wrist[0]
                    wrist_y = right_wrist[1]

                    x_diff = wrist_x - self._idle_wrist[0]
                    y_diff = wrist_y - self._idle_wrist[1]
                    abs_x_diff = abs(x_diff)
                    abs_y_diff = abs(y_diff)

                    # print("abs_x_diff - abs_y_diff", abs_x_diff - abs_y_diff)

                    if abs_x_diff == 0 or abs_y_diff == 0:
                        pass
                    else:
                        if abs_x_diff / abs_y_diff < 1.2 and abs_y_diff / abs_x_diff < 1.2:
                            self._current_status = ControlStatus.INVALID
                            return
                        else:
                            if abs_x_diff > abs_y_diff:
                                # print("x_diff", x_diff)
                                if x_diff > 0:
                                    self._current_status = ControlStatus.LEFT
                                else:
                                    self._current_status = ControlStatus.RIGHT
                            else:
                                # print("y_diff", y_diff)
                                if y_diff > 0:
                                    self._current_status = ControlStatus.DOWN
                                else:
                                    self._current_status = ControlStatus.UP

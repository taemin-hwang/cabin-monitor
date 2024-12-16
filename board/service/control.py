import math

from enum import Enum

class ControlStatus(Enum):
    IDLE = 0
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4
    INVALID = 5

class GameStatus(Enum):
    GAME_UP = 5
    GAME_RIGHT = 6
    GAME_LEFT = 7
    GAME_NECK = 8
    INVALID = 9

class Control:
    def __init__(self):
        self._current_status = ControlStatus.INVALID
        self._previous_status = ControlStatus.INVALID
        self._game_status = GameStatus.INVALID
        self._idle_elbow = [0, 0]
        self._idle_wrist = [0, 0]

    def get_control(self, keypoints):
        self.update_status(keypoints)

        control_status = self._current_status
        game_status = self.get_gamecontrol(keypoints)

        if self._current_status != self._previous_status:
            self._previous_status = self._current_status
        else:
            control_status = ControlStatus.INVALID

        if control_status == ControlStatus.INVALID and game_status == GameStatus.INVALID:
            return -1
        elif control_status != ControlStatus.INVALID:
            return control_status.value
        else:
            return game_status.value

    def get_distance(self, point1, point2):
        return math.sqrt(((point1[0]-point2[0])**2)+((point1[1]-point2[1])**2))

    def get_gamecontrol(self, keypoints):
        p_nose = keypoints[0] # nose
        p_leye = keypoints[2] # left_eye
        p_reye = keypoints[1] # right_eye
        p_lear = keypoints[4] # left_ear
        p_rear = keypoints[3] # right_ear
        p_lshoulder = keypoints[6]  # left_shoulder
        p_rshoulder = keypoints[5]  # right_shoulder
        p_lelbow = keypoints[8]     # left_elbow
        p_relbow = keypoints[7]     # right_elbow
        p_lwrist = keypoints[10]    # left_wrist
        p_rwrist = keypoints[9]     # right_wrist

        # 기본적으로 Z축(3차원)이 없으므로 2D 좌표를 기준으로 계산
        l_arm_height = p_lwrist[1] - p_lshoulder[1]  # 왼팔의 높이
        r_arm_height = p_rwrist[1] - p_rshoulder[1]  # 오른팔의 높이

        # print("p_nose : ", p_nose)
        # print("p_leye : ", p_leye)
        # print("p_reye : ", p_reye)
        # print("p_lear : ", p_lear)
        # print("p_rear : ", p_rear)
        # print("p_lshoulder : ", p_lshoulder)
        # print("p_rshoulder : ", p_rshoulder)
        # print("p_lelbow : ", p_lelbow)
        # print("p_relbow : ", p_relbow)
        # print("p_lwrist : ", p_lwrist)
        # print("p_rwrist : ", p_rwrist)

        # 팔을 위로 뻗은 상태인지 확인
        status = GameStatus.INVALID

        if ((p_lelbow[1] > 10 and p_lelbow[1] < 80 and p_relbow[1] > 10 and p_relbow[1] < 80) or
            (p_lwrist[1] > 10 and p_lwrist[1] < 80 and p_rwrist[1] > 10 and p_rwrist[1] < 80)):
            status = GameStatus.GAME_UP
            if (p_lwrist[0] < 110 ):
                status = GameStatus.GAME_RIGHT
            elif (p_rwrist[0] > 110 ):
                status = GameStatus.GAME_LEFT
        elif ((p_lear[1] > 10 and p_rear[1] > 10 and p_lear[1] - p_rear[1] > 10) or 
            (p_lear[1] > 10 and p_rear[1] > 10 and p_rear[1] - p_lear[1] > 10)):
            status = GameStatus.GAME_NECK

        return status

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
                            # else:
                            #     # print("y_diff", y_diff)
                            #     if y_diff > 0:
                            #         self._current_status = ControlStatus.DOWN
                            #     else:
                            #         self._current_status = ControlStatus.UP

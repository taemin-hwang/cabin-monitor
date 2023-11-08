import numpy as np
import math

class Status:
    def __init__(self):
        self._status = 1
        pass

    def get_status(self, keypoints):
        p_nose = keypoints[0] # nose
        p_leye = keypoints[1] # left_eye
        p_reye = keypoints[2] # right_eye
        p_lear = keypoints[3] # left_ear
        p_rear = keypoints[4] # right_ear
        p_lshoulder = keypoints[5]
        p_rshoulder = keypoints[6]

        d1 = math.sqrt(((p_leye[0]-p_lear[0])**2)+((p_leye[1]-p_lear[1])**2))
        d2 = math.sqrt(((p_reye[0]-p_rear[0])**2)+((p_reye[1]-p_rear[1])**2))
        d_shoulder = math.sqrt(((p_lshoulder[0]-p_rshoulder[0])**2)+((p_lshoulder[1]-p_rshoulder[1])**2))

        status = 1

        if d1 == 0 or d2 == 0 or d_shoulder == 0:
            return self._status

        d1_ratio = d1 / d_shoulder
        d2_ratio = d2 / d_shoulder

        # print("p_leye[0]", p_leye[0])
        # print("p_lear[0]", p_lear[0])
        # print("p_reye[0]", p_reye[0])
        # print("p_rear[0]", p_rear[0])

        if (d1_ratio < 0.04 or d2_ratio < 0.04) :
            status = 2
        elif (p_leye[0] > p_lear[0] or p_reye[0] < p_rear[0]):
            status = 2
        else:
            status = 1

        # print("status : ", status)

        self._status = status
        return self._status
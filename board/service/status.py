import numpy as np
import math

    # 0// nose
    # 1// reye
    # 2// leye
    # 3// rear
    # 4// lear
    # 5// rsoulder
    # 6// lsoulder
    # 7// relbow
    # 8// lelbow
    # 9// rwrist
    # 10// lwrist

class Status:
    def __init__(self):
        self._status = 1
        pass

    def get_status(self, keypoints):
        p_nose = keypoints[0] # nose
        p_leye = keypoints[2] # left_eye
        p_reye = keypoints[1] # right_eye
        p_lear = keypoints[4] # left_ear
        p_rear = keypoints[3] # right_ear
        p_lshoulder = keypoints[6]
        p_rshoulder = keypoints[5]

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

        # print("d1_ratio", d1_ratio)
        # print("d2_ratio", d2_ratio)

        # print("d1/d2", d1/d2)

        # if (d1_ratio < 0.04 or d2_ratio < 0.04) :
        #     status = 2
        # elif (p_leye[0] > p_lear[0] or p_reye[0] < p_rear[0]):
        #     status = 2
        if (d1/d2 >= 0.6 and d2/d1 >= 0.6):
            status = 1
        else:
            status = 2

        # print("status : ", status)

        self._status = status
        return self._status
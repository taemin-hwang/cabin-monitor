import math

class Status:
    def __init__(self):
        pass

    def get_status(self, keypoints):
        p_nose = keypoints[0] # nose
        p_leye = keypoints[1] # left_eye
        p_reye = keypoints[2] # right_eye
        p_lear = keypoints[3] # left_ear
        p_rear = keypoints[4] # right_ear

        d1 = math.sqrt(((p_nose[0]-p_lear[0])**2)+((p_nose[1]-p_lear[1])**2))
        d2 = math.sqrt(((p_nose[0]-p_rear[0])**2)+((p_nose[1]-p_rear[1])**2))

        status = 1

        if (d2 / d1 > 1.4) :
            status = 2
        elif (d1 / d2 > 1.4) :
            status = 3
        else:
            status = 1

        return status
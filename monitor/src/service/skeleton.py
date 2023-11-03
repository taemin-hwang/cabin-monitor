import cv2
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

# Keypoints18
# "0: nose"
# "1: left_eye"
# "2: right_eye"
# "3: left_ear"
# "4: right_ear"
# "5: left_shoulder"
# "6: right_shoulder"
# "7: left_elbow"
# "8: right_elbow"
# "9: left_wrist"
# "10: right_wrist"
# "11: left_hip"
# "12: right_hip"
# "13: left_knee"
# "14: right_knee"
# "15: left_ankle"
# "16: right_ankle"
# "17: neck"


class Skeleton:
    def __init__(self):
        pass

    def get_annotations(self, image):
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        return results

    def get_skeleton(self, annotations):
        skeleton = np.zeros((33, 3))

        for i, landmark in enumerate(annotations.pose_landmarks.landmark):
            if landmark is not None:
                skeleton[i] = [landmark.x, landmark.y, landmark.visibility]

        # convert 33 keypoints to 18 keypoints
        skeleton_18 = np.zeros((18, 3))
        skeleton_18[0] = skeleton[0]
        skeleton_18[1] = skeleton[2]
        skeleton_18[2] = skeleton[5]
        skeleton_18[3] = skeleton[7]
        skeleton_18[4] = skeleton[8]
        skeleton_18[5] = skeleton[11]
        skeleton_18[6] = skeleton[12]
        skeleton_18[7] = skeleton[13]
        skeleton_18[8] = skeleton[14]
        skeleton_18[9] = skeleton[15]
        skeleton_18[10] = skeleton[16]
        skeleton_18[11] = skeleton[23]
        skeleton_18[12] = skeleton[24]
        skeleton_18[13] = skeleton[25]
        skeleton_18[14] = skeleton[26]
        skeleton_18[15] = skeleton[27]
        skeleton_18[16] = skeleton[28]
        skeleton_18[17] = (skeleton[12] + skeleton[11]) / 2 # neck

        return skeleton_18
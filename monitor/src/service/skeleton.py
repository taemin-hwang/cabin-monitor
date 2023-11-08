import cv2
import mediapipe as mp
import numpy as np
import math

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
        self.pose = mp_pose.Pose(
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5)

    def get_annotations(self, image):
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = self.pose.process(image)
        return results

    def get_skeleton(self, image, annotations):
        skeleton = np.zeros((33, 3))

        for i, landmark in enumerate(annotations.pose_landmarks.landmark):
            if landmark is not None:
                skeleton[i] = [landmark.x, landmark.y, landmark.visibility]

        skeleton_33 = np.zeros((33, 3))
        for i, keypoint in enumerate(skeleton):
            keypoint_px = self._normalized_to_pixel_coordinates(keypoint[0], keypoint[1], image.shape[1], image.shape[0])
            if keypoint_px is None:
                continue
            skeleton_33[i] = [keypoint_px[0], keypoint_px[1], keypoint[2]]

        # convert 33 keypoints to 18 keypoints
        skeleton_18 = np.zeros((18, 3))
        skeleton_18[0] = skeleton_33[0]
        skeleton_18[1] = skeleton_33[2]
        skeleton_18[2] = skeleton_33[5]
        skeleton_18[3] = skeleton_33[7]
        skeleton_18[4] = skeleton_33[8]
        skeleton_18[5] = skeleton_33[11]
        skeleton_18[6] = skeleton_33[12]
        skeleton_18[7] = skeleton_33[13]
        skeleton_18[8] = skeleton_33[14]
        skeleton_18[9] = skeleton_33[15]
        skeleton_18[10] = skeleton_33[16]
        skeleton_18[11] = skeleton_33[23]
        skeleton_18[12] = skeleton_33[24]
        skeleton_18[13] = skeleton_33[25]
        skeleton_18[14] = skeleton_33[26]
        skeleton_18[15] = skeleton_33[27]
        skeleton_18[16] = skeleton_33[28]
        skeleton_18[17] = (skeleton_33[12] + skeleton_33[11]) / 2 # neck

        return skeleton_18

    def get_skeleton_11(self, skeleton_18):
        skeleton_11 = np.zeros((11, 3))
        skeleton_11[0] = skeleton_18[0] # nose
        # reye
        # leye
        # rear
        # lear
        # rshoulder
        # lshoulder
        # relbow
        # lelbow
        # rwrist
        # lwrist
        skeleton_11[1] = skeleton_18[2]
        skeleton_11[2] = skeleton_18[1]
        skeleton_11[3] = skeleton_18[4]
        skeleton_11[4] = skeleton_18[3]
        skeleton_11[5] = skeleton_18[6]
        skeleton_11[6] = skeleton_18[5]
        skeleton_11[7] = skeleton_18[8]
        skeleton_11[8] = skeleton_18[7]
        skeleton_11[9] = skeleton_18[10]
        skeleton_11[10] = skeleton_18[9]
        return skeleton_11


    def _normalized_to_pixel_coordinates(self, normalized_x: float, normalized_y: float, image_width: int, image_height: int):

        # Checks if the float value is between 0 and 1.
        def is_valid_normalized_value(value: float) -> bool:
            return (value > 0 or math.isclose(0, value)) and (value < 1 or math.isclose(1, value))

        if not (is_valid_normalized_value(normalized_x) and
                is_valid_normalized_value(normalized_y)):
            # TODO: Draw coordinates even if it's outside of the image bounds.
            return None
        x_px = min(math.floor(normalized_x * image_width), image_width - 1)
        y_px = min(math.floor(normalized_y * image_height), image_height - 1)
        return x_px, y_px
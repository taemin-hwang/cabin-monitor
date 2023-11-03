import cv2
import mediapipe as mp
import numpy as np
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

class Skeleton:
    def __init__(self):
        pass

    def get_skeleton(self, image):
        pose = mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        # To improve performance, optionally mark the image as not writeable to
        # pass by reference.
        image.flags.writeable = False
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        results = pose.process(image)
        return results

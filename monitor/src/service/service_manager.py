import cv2
import math
import numpy as np
import mediapipe as mp

mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

from service.skeleton import Skeleton
from service.control import Control
from service.status import Status
from service.voice import Voice

class ServiceManager:
    def __init__(self):
        self.skeleton = Skeleton()
        self.control = Control()
        self.status = Status()
        self.voice = Voice()

        self.__skeleton = None
        self.__control = None
        self.__status = None

        self.is_updated = False

    def run(self, image):
        annotations = self.skeleton.get_annotations(image)
        if annotations is None or annotations.pose_landmarks is None:
            self.is_updated = False
            return

        self.is_updated = True

        skeleton_18 = self.skeleton.get_skeleton(image, annotations)
        self.__control = self.control.get_control(skeleton_18)
        self.__status = self.status.get_status(skeleton_18)
        self.__skeleton = self.skeleton.get_skeleton_11(skeleton_18)

        # background = np.ones((image.shape[0], image.shape[1], 3), dtype=np.uint8) * 50
        self.draw_skeleton(image, self.__skeleton)
        return image

    def draw_skeleton(self, image, skeleton):
        # Draw the pose annotation on the image.

        color = (232, 176, 59)
        for keypoint in skeleton:
            # keypoint_px = self._normalized_to_pixel_coordinates(keypoint[0], keypoint[1], image.shape[1], image.shape[0])
            if keypoint is None or keypoint[2] == 0:
                continue
            if keypoint[0] > image.shape[1] or keypoint[1] > image.shape[0]:
                continue
            if keypoint[0] < 0 or keypoint[1] < 0:
                continue

            cv2.circle(image, (int(keypoint[0]), int(keypoint[1])), 5, color, -1)

        bone = [
            (0, 1),
            (1, 3),
            (0, 2),
            (2, 4),
            (0, 5),
            (0, 6),
            (5, 7),
            (7, 9),
            (6, 8),
            (8, 10),
            (5, 6)
        ]

        for start, end in bone:
            keypoint_start = skeleton[start]
            keypoint_end = skeleton[end]

            # keypoint_px_start = self._normalized_to_pixel_coordinates(keypoint_start[0], keypoint_start[1], image.shape[1], image.shape[0])
            if keypoint_start is None or keypoint_start[2] == 0:
                continue
            if keypoint_start[0] > image.shape[1] or keypoint_start[1] > image.shape[0]:
                continue
            if keypoint_start[0] < 0 or keypoint_start[1] < 0:
                continue

            # keypoint_px_end = self._normalized_to_pixel_coordinates(keypoint_end[0], keypoint_end[1], image.shape[1], image.shape[0])
            if keypoint_end is None or keypoint_end[2] == 0:
                continue
            if keypoint_end[0] > image.shape[1] or keypoint_end[1] > image.shape[0]:
                continue
            if keypoint_end[0] < 0 or keypoint_end[1] < 0:
                continue

            cv2.line(image, (int(keypoint_start[0]), int(keypoint_start[1])), (int(keypoint_end[0]), int(keypoint_end[1])), color, 2)

    def get_skeleton(self):
        if self.__skeleton is None:
            print("skeleton is None")
            return None
        return self.__skeleton

    def get_control(self):
        if self.__control is None:
            print("control is None")
            return None
        return self.__control

    def get_status(self):
        if self.__status is None:
            print("status is None")
            return None
        return self.__status

    def get_voice(self):
        return self.voice.get_voice()

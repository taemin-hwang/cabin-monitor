import cv2
import numpy as np
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

from service.skeleton import Skeleton
from service.control import Control
from service.status import Status

class CabinMonitor:
    def __init__(self):
        self.skeleton = Skeleton()
        self.control = Control()
        self.status = Status()

    def run(self):
        # For webcam input:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            annotations = self.skeleton.get_annotations(image)
            if annotations is None or annotations.pose_landmarks is None:
                continue

            self.draw_pose_annotation(np.ones(image.shape, dtype=np.uint8)*50, annotations)

            skeleton = self.skeleton.get_skeleton(annotations)
            control = self.control.get_control(skeleton)
            status = self.status.get_status(skeleton)


            if cv2.waitKey(1) == ord('q'):
                break

        cap.release()

    def draw_pose_annotation(self, image, results):
        # Draw the pose annotation on the image.
        mp_drawing.draw_landmarks(
            image,
            results.pose_landmarks,
            mp_pose.POSE_CONNECTIONS,
            landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
        # Flip the image horizontally for a selfie-view display.
        cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))
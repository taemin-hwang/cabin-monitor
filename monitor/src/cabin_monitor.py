import cv2
import numpy as np
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

from service.skeleton import Skeleton

class CabinMonitor:
    def __init__(self):
        self.skeleton = Skeleton()

    def run(self):
        # For webcam input:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            results = self.skeleton.get_skeleton(image)

            # Make white background
            black = np.zeros(image.shape, dtype=np.uint8)

            # Draw the pose annotation on the image.
            mp_drawing.draw_landmarks(
                black,
                results.pose_landmarks,
                mp_pose.POSE_CONNECTIONS,
                landmark_drawing_spec=mp_drawing_styles.get_default_pose_landmarks_style())
            # Flip the image horizontally for a selfie-view display.
            cv2.imshow('MediaPipe Pose', cv2.flip(black, 1))

            if cv2.waitKey(1) == ord('q'):
                break
        cap.release()
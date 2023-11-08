import cv2
import numpy as np
import mediapipe as mp
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles
mp_pose = mp.solutions.pose

from service.service_manager import ServiceManager
from transfer.transfer_manager import TransferManager

class CabinMonitor:
    def __init__(self):
        self.service_manager = ServiceManager()
        self.transfer_manager = TransferManager()
        self.__current_status = 1

    def run(self):
        self.transfer_manager.init()
        self.transfer_manager.set_recv_handler(self.service_manager.get_voice)

        # For webcam input:
        cap = cv2.VideoCapture(0)

        while cap.isOpened():
            success, image = cap.read()
            if not success:
                print("Ignoring empty camera frame.")
                continue

            # resize image to 640 x 480
            image = cv2.resize(image, (640, 480))

            self.service_manager.run(image)
            if (self.service_manager.is_updated):
                skeleton = self.service_manager.get_skeleton()
                control = self.service_manager.get_control()
                status = self.service_manager.get_status()
                gaze = self.service_manager.get_gaze()

                self.transfer_manager.run(skeleton, control, status, gaze)

                self.print_control(control)
                self.print_status(status)

            cv2.imshow('MediaPipe Pose', cv2.flip(image, 1))

            if cv2.waitKey(1) == ord('q'):
                break

        cap.release()

    def print_control(self, control):
        if control == 1:
            print("Control : UP")
        elif control == 2:
            print("Control : DOWN")
        elif control == 3:
            print("Control : LEFT")
        elif control == 4:
            print("Control : RIGHT")
        else:
            pass

    def print_status(self, status):
        if status is not self.__current_status:
            if status == 2:
                print("Status : GAZE LEFT")
            elif status == 3:
                print("Status : GAZE RIGHT")

        self.__current_status = status

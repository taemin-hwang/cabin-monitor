import cv2
import math
import numpy as np

from service.control import Control
from service.status import Status
from service.voice import Voice
from service.gaze import Gaze

class ServiceManager:
    def __init__(self):
        self.control = Control()
        self.status = Status()
        self.voice = Voice()
        self.gaze = Gaze()

        self.__skeleton = None
        self.__control = None
        self.__status = None
        self.__gaze = None

        self.is_updated = False

    def update_service(self, skeleton):
        self.__skeleton = skeleton
        self.__control = self.control.get_control(self.__skeleton)
        self.__status = self.status.get_status(self.__skeleton)
        self.__gaze = self.gaze.estimate_pose(self.__skeleton)

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

    def get_gaze(self):
        if self.__gaze is None:
            print("gaze is None")
            return None
        return self.__gaze

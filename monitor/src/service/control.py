from service.rule.body_gesture_manager import BodyGestureManager


class Control:
    def __init__(self):
        self.__body_gesture_manager = BodyGestureManager()

    def get_control(self, keypoints):
        return self.__body_gesture_manager.classify_gesture(keypoints)
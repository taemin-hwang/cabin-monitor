import numpy as np

class Gaze:
    def __init__(self):
        self.__reference_distances = {
            'eye': 40,
            'eye_to_nose': 30,
        }


    def estimate_pose(self, keypoints):
        # Extract the keypoints
        left_eye = keypoints[1] # left_eye
        right_eye = keypoints[2] # right_eye
        nose = keypoints[0] # nose
        left_ear = keypoints[3] # left_ear
        right_ear = keypoints[4] # right_ear

        # print("eye_to_nose", np.linalg.norm(keypoints[1] - keypoints[0]))
        # print("eye_to_eye", np.linalg.norm(keypoints[1] - keypoints[2]))

        # Calculate pitch
        eye_nose_distance = (np.linalg.norm(nose - left_eye) + np.linalg.norm(nose - right_eye)) / 2
        pitch_degrees = (self.__reference_distances['eye_to_nose'] - eye_nose_distance) * 90 / self.__reference_distances['eye_to_nose']

        # Calculate yaw
        eye_distance = np.linalg.norm(right_eye - left_eye)
        yaw_degrees = (1 - (eye_distance / self.__reference_distances['eye'])) * 180

        left_ear_distance = np.linalg.norm(left_eye - left_ear)
        right_ear_distance = np.linalg.norm(right_eye - right_ear)

        if left_ear_distance > right_ear_distance:  # Adjust the yaw angle based on the direction the face is turned
            yaw_degrees = -yaw_degrees

        # print("roll_degrees", roll_degrees)
        # print("pitch_degrees", pitch_degrees)
        # print("yaw_degrees", yaw_degrees)

        return int(yaw_degrees)
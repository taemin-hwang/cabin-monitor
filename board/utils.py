from datetime import datetime
import os
from enum import Enum

DEFAULT_PORT = 8888
DEFAULT_BUFLEN = 1460 * 2
IMAGE_WIDTH = 192
IMAGE_HEIGHT = 256
HEATMAP_WIDTH = 48
HEATMAP_HEIGHT = 64
NUM_KEYPOINTS = 11
MOVING_AVERAGE_WINDOW = 1  # 이동 평균 윈도우 크기

class BODY_PARTS_11(Enum):
    NOSE = 0
    RIGHT_EYE = 1
    LEFT_EYE = 2
    RIGHT_EAR = 3
    LEFT_EAR = 4
    RIGHT_SHOULDER = 5
    LEFT_SHOULDER = 6
    RIGHT_ELBOW = 7
    LEFT_ELBOW = 8
    RIGHT_WRIST = 9
    LEFT_WRIST = 10

BODY_BONES_POSE_11 = [
    (BODY_PARTS_11.LEFT_EAR, BODY_PARTS_11.LEFT_EYE),
    (BODY_PARTS_11.LEFT_EYE, BODY_PARTS_11.NOSE),
    (BODY_PARTS_11.RIGHT_EYE, BODY_PARTS_11.NOSE),
    (BODY_PARTS_11.RIGHT_EYE, BODY_PARTS_11.NOSE),
    (BODY_PARTS_11.LEFT_SHOULDER, BODY_PARTS_11.RIGHT_SHOULDER),
    (BODY_PARTS_11.LEFT_SHOULDER, BODY_PARTS_11.LEFT_ELBOW),
    (BODY_PARTS_11.LEFT_ELBOW, BODY_PARTS_11.LEFT_WRIST),
    (BODY_PARTS_11.RIGHT_SHOULDER, BODY_PARTS_11.RIGHT_ELBOW),
    (BODY_PARTS_11.RIGHT_ELBOW, BODY_PARTS_11.RIGHT_WRIST),
]

def create_log_folder():
    # 현재 날짜와 시간을 yymmddhhmmss 형식으로 가져옴
    current_time = datetime.now().strftime("%y%m%d%H%M%S")
    # 폴더 이름을 생성
    folder_name = f"log-{current_time}"

    # 폴더 생성
    os.makedirs(folder_name, exist_ok=True)
    print(f"Folder '{folder_name}' created successfully.")
    return folder_name
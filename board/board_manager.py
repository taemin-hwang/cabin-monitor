import socket
import struct
import numpy as np
import cv2
from PIL import Image
import os
import re
from sklearn.cluster import DBSCAN
from collections import deque
import threading
import copy
import concurrent.futures
import time
import speech_recognition as sr
import logging
from collections import defaultdict

from utils import *

from service.service_manager import ServiceManager
from transfer.transfer_manager import TransferManager

# Logging 설정
logging.basicConfig(filename='chunk_logging.log', level=logging.INFO, format='%(asctime)s - %(message)s')

class BoardManager:
    def __init__(self, config):
        self.load = config["load"]
        self.start_fid = 0
        self.addr_file = os.path.join('./', 'out_addr.txt')
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        output_video_name = f"./log/log-{current_time}.mp4"
        frame_size = (768, 512)
        # if self.load is None:
        #     self.video_writer = VideoWriter(output_video_name, frame_size, 10)
        # else:
        #     self.video_writer = None
        self.skeleton_buffer = np.zeros((4, 7, 11, 3)) # 10개의 프레임에 대한 11개의 keypoint의 x, y 좌표를 저장

        self.service_managers = [ServiceManager() for _ in range(4)]
        self.transfer_manager = TransferManager()
        self.__current_status = 1

        # 설정: 깨어날 키워드
        self.WAKE_WORD = "hey kitty"  # hey KETI

        # 음성 인식을 위한 스레드 시작
        self.voice_thread = threading.Thread(target=self.listen_for_wake_word)
        self.voice_thread.daemon = True
        self.voice_thread.start()

        self.stx_0x02_count = 0  # 채널별 호출 횟수 저장
        self.start_time = time.time()  # 시작 시간 기록

    def init(self):
        self.transfer_manager.init()
        if self.load is not None:
            self.start_fid, self.end_fid = self.get_frame_id_range(self.load)
            print(f"Read from {self.start_fid:06d} to {self.end_fid:06d} in {self.load}")

        # 각 채널과 cnt 별로 패킷 데이터를 저장할 배열
        self.packet_data_image = {ch: [None] * 104 for ch in range(4)}
        self.packet_data_heatmap = {ch: [None] * 24 for ch in range(4)}

    def shutdown(self):
        self.transfer_manager.shutdown()

    def listen_for_wake_word(self):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            print("[1] Listening for wake word...")
            while True:
                try:
                    audio = recognizer.listen(source)
                    recognized_text = recognizer.recognize_google(audio)
                    print(f"[1] Recognized: {recognized_text}")
                    
                    if self.WAKE_WORD in recognized_text.lower():
                        print("[1] Wake word detected! Listening for command...")
                        self.listen_for_commands()  # 명령을 수신하는 함수 호출

                except sr.UnknownValueError:
                    print("[1] Sorry, I did not catch that.")
                except sr.RequestError:
                    print("[1] Could not request results from Google Speech Recognition service.")

    def listen_for_commands(self):
        recognizer = sr.Recognizer()
        self.transfer_manager.send_voice("Hey KETI")
        with sr.Microphone() as source:
            print("[2] Waiting for commands...")
            start_time = time.time()
            while True:
                try:
                    audio = recognizer.listen(source, timeout=5)
                    recognized_text = recognizer.recognize_google(audio, language='ko-KR')
                    print(f"[2] Command recognized: {recognized_text}")

                    self.transfer_manager.send_voice(recognized_text)
                    print("[2] Voice command sent to TransferManager.")
                    break  # 명령 인식 후 반복 종료

                except sr.UnknownValueError:
                    print("[2] Sorry, I did not catch that.")
                except sr.RequestError:
                    print("[2] Could not request results from Google Speech Recognition service.")
                except sr.WaitTimeoutError:
                    print("[2] No command detected. Going back to listening for wake word...")
                    return

    def run(self):
        frame_id = self.start_fid
        self.step_wise = False
        self.toggle = False

        window_name = "HVI OUT"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 700, 500)

        # if self.load is None:
        # folder = self.create_log_folder()

        # 데이터 수신 및 처리 작업을 병렬로 수행
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            futures = [executor.submit(self.make_chunk, i) for i in range(1)]
            print("ready to make chunk")

            # 이미지 저장 스레드 시작
            # save_thread = threading.Thread(target=self.periodic_save)
            # save_thread.daemon = True
            # save_thread.start()

            while True:
                combined_image, skeletons = self.combine_channel_images(self.packet_data_image, self.packet_data_heatmap)

                for ch in range(4):
                    if skeletons.get(ch) is not None:
                        self.service_managers[ch].update_service(skeletons[ch])
                        skeleton = self.service_managers[ch].get_skeleton()
                        control = self.service_managers[ch].get_control()
                        status = self.service_managers[ch].get_status()
                        gaze = self.service_managers[ch].get_gaze()
                        self.transfer_manager.run(ch, skeleton, control, status, gaze)
                        # print(ch, " =========== ")
                        # self.print_control(control)
                        # self.print_status(status)
                        time.sleep(0.01)

                cv2.imshow(window_name, combined_image)
                key = cv2.waitKey(1)
                frame_id += 1
                if self.load is not None and not self.step_wise and key == ord('s'):
                    self.step_wise = True
                if key == ord('q'):
                    # self.video_writer.release()
                    break
                if self.step_wise:
                    while True:
                        key = cv2.waitKey(1)
                        if key == ord('s'):
                            self.toggle = not self.toggle
                            break
                        elif key == ord('a'):
                            self.step_wise = False
                            break

            for future in futures:
                future.cancel()

        cv2.destroyAllWindows()

    def periodic_save(self, folder=None):
        frame_id = 0
        while True:
            time.sleep(0.1)  # 1초 간격으로 실행
            for ch in range(4):
                # 깊은 복사로 현재 데이터를 저장
                image_copy = [copy.deepcopy(pkt) for pkt in self.packet_data_image[ch] if pkt is not None]
                heatmap_copy = [copy.deepcopy(pkt) for pkt in self.packet_data_heatmap[ch] if pkt is not None]
                if image_copy and heatmap_copy:
                    combined_image, _ = self.combine_channel_images(self.packet_data_image, self.packet_data_heatmap)
                    # if self.video_writer is not None:
                    # self.video_writer.write_frame(combined_image)
                    # if len(image_copy) >= IMAGE_WIDTH * IMAGE_HEIGHT * 3:
                    #     self.save_image_and_heatmap(folder, ch, frame_id, image_copy, heatmap_copy)
            frame_id += 1

    def make_chunk(self, i):
        print(f"make chunk {i}")
        total_bytes = IMAGE_WIDTH * IMAGE_HEIGHT * 3
        frame_id = 0
        while True:
            if self.load is None:
                stx, length_field, ch, count, payload, csum, etx = self.transfer_manager.get_data()

                if stx is None or ch > 3:
                    print("stx is None or ch > 3")
                    print("ch : ", ch)
                    continue

                if stx == 0x20:
                    # if count == 103:
                        # print(f"Received full image for channel {ch}")
                    self.packet_data_image[ch][count] = payload
                elif stx == 0x02:
                    # if count == 13:
                        # print(f"Received full hvi for channel {ch}")
                    self.packet_data_heatmap[ch][count] = payload
                    if count == 23:
                        self.stx_0x02_count += 1
                        # 1초 단위로 호출 횟수 로깅
                        # self.log_stx_0x02_count()
            else:
                if frame_id >= self.end_fid:
                    break

                if self.step_wise:
                    if not self.toggle:
                        time.sleep(0.1)
                        continue
                    else:
                        for ch in range(4):
                            self.packet_data_image[ch], self.packet_data_heatmap[ch] = self.read_file(ch, frame_id)
                        frame_id += 1
                        self.toggle = not self.toggle
                else:
                    for ch in range(4):
                        self.packet_data_image[ch], self.packet_data_heatmap[ch] = self.read_file(ch, frame_id)
                    frame_id += 1
                time.sleep(0.1)

    def log_stx_0x02_count(self):
        """1초 동안 stx == 0x02가 호출된 횟수를 로깅합니다."""
        elapsed_time = time.time() - self.start_time
        if elapsed_time >= 1:  # 1초 경과 확인
            logging.info(f"stx == 0x02 count for channel : {self.stx_0x02_count}")
            self.stx_0x02_count = 0  # 카운트 초기화
            self.start_time = time.time()  # 시작 시간 갱신

    def read_file(self, ch, frame_id):
        image_filename = f"image-{frame_id:06d}-{ch}.bin"
        heatmap_filename = f"heatmap-{frame_id:06d}-{ch}.bin"

        # 파일 경로 생성
        image_path = os.path.join(self.load, image_filename)
        heatmap_path = os.path.join(self.load, heatmap_filename)

        if not os.path.exists(image_path) or not os.path.exists(heatmap_path):
            print("No such file or directory")
            print(" - ", image_path)
            print(" - ", heatmap_path)
            return [None] * 104, [None] * 24
        else:
            print("Read from ", image_path)
            print("Read from ", heatmap_path)

        image_array = np.fromfile(image_path, dtype='int8')
        heatmap_array  = np.fromfile(heatmap_path, dtype='int8')

        return image_array, heatmap_array

    def get_frame_id_range(self, load_folder, ch=0):
        # 정규 표현식을 사용하여 파일 이름에서 frame_id를 추출
        pattern = re.compile(rf'image-(\d{{6}})-{ch}')

        frame_ids = []

        for filename in os.listdir(load_folder):
            match = pattern.match(filename)
            if match:
                frame_id = int(match.group(1))
                frame_ids.append(frame_id)

        if not frame_ids:
            return None, None

        start_frame_id = min(frame_ids)
        end_frame_id = max(frame_ids)

        return start_frame_id, end_frame_id

    def visualize_heatmaps(self, heatmap, image):
        colors = [
            [1, 0, 0],    # Red
            [0, 1, 0],    # Green
            [0, 0, 1],    # Blue
            [1, 1, 0],    # Yellow
            [1, 0, 1],    # Magenta
            [0, 1, 1],    # Cyan
            [1, 0.5, 0],  # Orange
            [0.5, 0, 1],  # Purple
            [0.5, 1, 0],  # Lime
            [0, 0.5, 1],  # Sky Blue
            [0.5, 0.5, 0] # Olive
        ]

        heatmap_resized = np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, NUM_KEYPOINTS))
        for i in range(NUM_KEYPOINTS):
            heatmap_resized[:, :, i] = np.array(Image.fromarray(heatmap[:, :, i]).resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.BILINEAR))

        heatmap_resized = (heatmap_resized - np.min(heatmap_resized)) / (np.max(heatmap_resized) - np.min(heatmap_resized))

        overlay_image = np.zeros_like(image, dtype=np.float32)
        for i in range(NUM_KEYPOINTS):
            for c in range(3):
                overlay_image[:, :, c] += heatmap_resized[:, :, i] * colors[i][c]

        blended_image = 0.5 * image.astype(np.float32) / 255.0 + 0.5 * overlay_image
        blended_image = np.clip(blended_image, 0, 1)

        return (blended_image * 255).astype(np.uint8)

    def visualize_skeleton(self, skeleton, heatmap_image):
        colors = [
            (255, 0, 0),       # Red
            (0, 255, 0),       # Green
            (0, 0, 255),       # Blue
            (255, 255, 0),     # Yellow
            (255, 0, 255),     # Magenta
            (0, 255, 255),     # Cyan
            (255, 128, 0),     # Orange
            (128, 0, 255),     # Purple
            (128, 255, 0),     # Lime
            (0, 128, 255),     # Sky Blue
            (128, 128, 0)      # Olive
        ]

        c_thres = 0.33
        for i in range(NUM_KEYPOINTS):
            x, y, c = skeleton[i]
            if all(coord > 0 for coord in [x, y]):
                if c > c_thres:
                    cv2.circle(heatmap_image, (int(x), int(y)), 3, colors[i], -1)
            # cv2.circle(heatmap_image, (x, y), 3, colors[i], -1)
            # cv2.putText(heatmap_image, str(i), (avg_x + 5, avg_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1, cv2.LINE_AA)

        for str_bone_id, dst_bone_id in BODY_BONES_POSE_11:
            str_bone_x, str_bone_y, str_score = skeleton[str_bone_id.value]
            dst_bone_x, dst_bone_y, dst_score = skeleton[dst_bone_id.value]

            if all(coord > 0 for coord in [str_bone_x, str_bone_y, dst_bone_x, dst_bone_y]):
                if str_score > c_thres and dst_score > c_thres:
                    cv2.line(heatmap_image, (int(str_bone_x), int(str_bone_y)), (int(dst_bone_x), int(dst_bone_y)), (255, 255, 255), 1)

        return heatmap_image

    def get_interpolated_skeleton(self, ch, skeleton):
        self.skeleton_buffer[ch] = np.roll(self.skeleton_buffer[ch], shift=1, axis=0)
        if skeleton is not np.zeros((11, 3)):
            self.skeleton_buffer[ch][0] = skeleton

        # next_skeleton = self.skeleton_buffer[ch][0]
        # curr_skeleton = self.skeleton_buffer[ch][1]
        # prev_skeleton = self.skeleton_buffer[ch][2]

        # for i in range(NUM_KEYPOINTS):
        #     diff_next_and_prev = np.linalg.norm(next_skeleton[i, :2] - prev_skeleton[i, :2])
        #     diff_next_and_curr = np.linalg.norm(next_skeleton[i, :2] - curr_skeleton[i, :2])
        #     # print("diff_next_and_prev : ", diff_next_and_prev)
        #     # print("diff_next_and_curr : ", diff_next_and_curr)
        #     if diff_next_and_prev < 10 and diff_next_and_curr > 10:
        #         curr_skeleton[i] = next_skeleton[i] * 0.5 + prev_skeleton[i] * 0.5

        # average next and curr and prev
        mean_skeleton = np.mean(self.skeleton_buffer[ch], axis=0)

        return mean_skeleton

    def get_skeleton(self, heatmap):
        skeletons = np.zeros((11, 3))

        for i in range(NUM_KEYPOINTS):
            # 각 keypoint에 대해 DBSCAN 클러스터링
            points = np.argwhere(heatmap[:, :, i] > 0.2)
            if len(points) > 0:
                db = DBSCAN(eps=3, min_samples=2).fit(points)
                labels = db.labels_

                # 가장 큰 클러스터의 중심을 계산
                if len(labels) > 0 and np.any(labels >= 0):
                    largest_cluster = points[labels == np.argmax(np.bincount(labels[labels >= 0]))]
                    if len(largest_cluster) > 0:
                        # center_y, center_x = np.mean(largest_cluster, axis=0).astype(int)
                        max_y, max_x = largest_cluster[np.argmax(heatmap[largest_cluster[:, 0], largest_cluster[:, 1], i])]

                        # 중심 위치에 원을 그림
                        center = (int(max_x * IMAGE_WIDTH / HEATMAP_WIDTH), int(max_y * IMAGE_HEIGHT / HEATMAP_HEIGHT))
                        # self.keypoint_history[i].append(center)
                        # 이동 평균 적용
                        # avg_x = int(np.mean([pos[0] for pos in self.keypoint_history[i]]))
                        # avg_y = int(np.mean([pos[1] for pos in self.keypoint_history[i]]))
                        # cv2.putText(image, str(i), (avg_x + 5, avg_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1, cv2.LINE_AA)
                        skeletons[i][0] = center[0]
                        skeletons[i][1] = center[1]
                        skeletons[i][2] = np.mean(heatmap[largest_cluster[:, 0], largest_cluster[:, 1], i])

        # 좌우 인덱스를 바꾸기 위한 매핑
        flip_indices = {
            5: 6,  # 오른쪽 어깨 -> 왼쪽 어깨
            6: 5,  # 왼쪽 어깨 -> 오른쪽 어깨
            7: 8,  # 오른쪽 팔꿈치 -> 왼쪽 팔꿈치
            8: 7,  # 왼쪽 팔꿈치 -> 오른쪽 팔꿈치
            9: 10, # 오른쪽 손목 -> 왼쪽 손목
            10: 9  # 왼쪽 손목 -> 오른쪽 손목
        }

        # 좌우를 바꾼 스켈레톤 데이터 생성
        skeletons_flipped = np.copy(skeletons)

        for left, right in flip_indices.items():
            skeletons_flipped[left], skeletons_flipped[right] = skeletons[right], skeletons[left]


        return skeletons_flipped

    def combine_channel_images(self, packet_data_image, packet_data_heatmap):
        cam_images = []
        point_images = []
        skeletons = {}

        # Initialize
        for ch in range(4):
            cam_images.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))
            point_images.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))

        for ch in range(4):
            if any(packet_data_image[ch]):
                full_payload = b''.join([pkt for pkt in packet_data_image[ch] if pkt is not None])
                if len(full_payload) >= IMAGE_WIDTH * IMAGE_HEIGHT * 3:
                    image_array = np.frombuffer(full_payload[:IMAGE_WIDTH * IMAGE_HEIGHT * 3], dtype=np.uint8)
                    image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
                    cam_images[ch] = image

            if any(packet_data_heatmap[ch]):
                full_heatmap_payload = b''.join([pkt for pkt in packet_data_heatmap[ch] if pkt is not None])
                if len(full_heatmap_payload) >= HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS:
                    heatmap_array = np.frombuffer(full_heatmap_payload[:HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS], dtype=np.uint8)

                    heatmap = np.zeros((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS))
                    pos = 0
                    with open(self.addr_file, 'r') as fID_addr:
                        addr_list = np.zeros((64 * 48, 2), dtype=int)
                        for i in range(64):
                            for j in range(48):
                                addr = int(fID_addr.read(3), 16)
                                fID_addr.read(1)  # Read the newline character
                                addri = addr // 48
                                addrj = addr % 48
                                addr_list[i * 48 + j] = [addri, addrj]
                                for k in range(11):
                                    temp = heatmap_array[pos]
                                    heatmap[addri, addrj, k] = int.from_bytes(temp, byteorder='little') / 255.0
                                    pos += 1

                    skeleton = self.get_skeleton(heatmap)
                    skeletons[ch] = skeleton
                    # skeleton = self.get_interpolated_skeleton(ch, skeleton)
                    heatmap_image = self.visualize_heatmaps(heatmap, cam_images[ch])
                    heatmap_image = self.visualize_skeleton(skeleton, heatmap_image)
                    cv2.putText(heatmap_image, f"CH. {ch}", (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1, cv2.LINE_AA)
                    point_images[ch] = heatmap_image

        # 이미지와 skeleton을 결합하여 그리드 형태로 표시
        combined_top_row = cv2.hconcat([cam_images[0], point_images[0], cam_images[1], point_images[1]])
        combined_bottom_row = cv2.hconcat([cam_images[2], point_images[2], cam_images[3], point_images[3]])
        combined_image = cv2.vconcat([combined_top_row, combined_bottom_row])
        combined_image = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)

        return combined_image, skeletons

    def create_log_folder(self):
        # 현재 날짜와 시간을 yymmddhhmmss 형식으로 가져옴
        current_time = datetime.now().strftime("%y%m%d%H%M%S")
        # 폴더 이름을 생성
        folder_name = f"./log/log-{current_time}"

        # 폴더 생성
        os.makedirs(folder_name, exist_ok=True)
        print(f"Folder '{folder_name}' created successfully.")
        return folder_name

    def save_image_and_heatmap(self, folder, ch, frame_id, image_array, heatmap_array):
        # 파일 이름 생성
        # image_filename = f"image-{ch}-{frame_id:06d}.bin"
        image_array = b''.join([pkt for pkt in image_array if pkt is not None])
        image_array = np.frombuffer(image_array[:IMAGE_WIDTH * IMAGE_HEIGHT * 3], dtype=np.uint8)
        image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        heatmap_array = b''.join([pkt for pkt in heatmap_array if pkt is not None])
        heatmap_array = np.frombuffer(heatmap_array[:HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS], dtype=np.uint8)

        image_filename = f"image-{frame_id:06d}-{ch}.bin"
        heatmap_filename = f"heatmap-{frame_id:06d}-{ch}.bin"
        image_jpg_filename = f"image-{frame_id:06d}-{ch}.jpg"
        # output_jpg_filename = f"heatmap-{frame_id:06d}-{ch}.jpg"

        # 파일 경로 생성
        image_path = os.path.join(folder, image_filename)
        heatmap_path = os.path.join(folder, heatmap_filename)
        image_jpg_path = os.path.join(folder, image_jpg_filename)
        # output_jpg_path = os.path.join(folder, output_jpg_filename)

        print("save image and heatmap to", image_path)
        # 이미지 저장
        image_array.astype('int8').tofile(image_path)
        heatmap_array.astype('int8').tofile(heatmap_path)
        cv2.imwrite(image_jpg_path, image)
        # cv2.imwrite(output_jpg_path, combined_image)

    def print_control(self, control):
        if control == 1:
            print("Control : UP")
        elif control == 2:
            print("Control : DOWN")
        elif control == 3:
            print("Control : LEFT")
        elif control == 4:
            print("Control : RIGHT")
        elif control == 5:
            print("Game : UP")
        elif control == 6:
            print("Game : RIGHT")
        elif control == 7:
            print("Game : LEFT")
        elif control == 8:
            print("Game : NECK")
        else:
            pass

    def print_status(self, status):
        if status is not self.__current_status:
            if status == 2:
                print("Status : GAZE LEFT")
            elif status == 3:
                print("Status : GAZE RIGHT")

        self.__current_status = status


class VideoWriter:
    def __init__(self, output_path, frame_size, fps=30):
        self.output_path = output_path
        self.frame_size = frame_size
        self.fps = fps
        self.video_writer = cv2.VideoWriter(
            output_path,
            cv2.VideoWriter_fourcc(*'mp4v'),
            fps,
            frame_size
        )

    def write_frame(self, frame):
        print(frame.shape)
        print(self.frame_size)
        if frame.shape[1] != self.frame_size[0] or frame.shape[0] != self.frame_size[1]:
            raise ValueError("Frame size does not match initialized frame size")
        self.video_writer.write(frame)

    def release(self):
        self.video_writer.release()
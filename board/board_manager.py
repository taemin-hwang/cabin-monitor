import socket
import struct
import numpy as np
import cv2
from PIL import Image
import os
import re
from sklearn.cluster import DBSCAN
from collections import deque

from utils import *
from transfer_manager import TransferManager

class BoardManager:
    def __init__(self, config):
        self.load = config["load"]
        self.transfer_manager = TransferManager(port=DEFAULT_PORT)
        # 각 keypoint의 좌표를 저장할 큐
        self.keypoint_history = {i: deque(maxlen=MOVING_AVERAGE_WINDOW) for i in range(NUM_KEYPOINTS)}
        self.start_fid = 0
        self.addr_file = os.path.join('./', 'out_addr.txt')

    def init(self):
        self.transfer_manager.init()
        if self.load != "":
            self.start_fid, self.end_fid = self.get_frame_id_range(self.load)
            print(f"Read from {self.start_fid:06d} to {self.end_fid:06d} in {self.load}")

    def shutdown(self):
        self.transfer_manager.shutdown()

    def run(self):
        self.transfer_manager.run()

        frame_id = self.start_fid
        step_wise = False

        # 각 채널과 cnt 별로 패킷 데이터를 저장할 배열
        packet_data_image = {ch: [None] * 104 for ch in range(4)}
        packet_data_heatmap = {ch: [None] * 24 for ch in range(4)}

        window_name = "HVI OUT"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(window_name, 700, 500)

        total_bytes = IMAGE_WIDTH * IMAGE_HEIGHT * 3
        while True:
            if self.load == "":
                stx, length_field, ch, count, payload, csum, etx = self.transfer_manager.get_data()

                if stx is None or ch > 3:
                    print("stx is None or ch > 3")
                    print("ch : ", ch)
                    continue

                if stx == 0x20:
                    packet_data_image[ch][count] = payload
                    if count == 103:  # End of image
                        print(f"Received full image for channel {ch}")
                        full_payload = b''.join([pkt for pkt in packet_data_image[ch] if pkt is not None])

                        if len(full_payload) >= total_bytes:
                            # 전체 이미지를 결합하여 표시
                            combined_image = self.combine_channel_images(packet_data_image, packet_data_heatmap)
                            cv2.imshow(window_name, combined_image)

                            frame_id += 1
                        else:
                            print(f"Error: Incomplete image data received for channel {ch}.")

                elif stx == 0x02:
                    packet_data_heatmap[ch][count] = payload
            else:
                if frame_id >= self.end_fid:
                    break

                for ch in range(4):
                    packet_data_image[ch], packet_data_heatmap[ch] = self.read_file(ch, frame_id)

                combined_image = self.combine_channel_images(packet_data_image, packet_data_heatmap)
                cv2.imshow(window_name, combined_image)

                frame_id += 1

            key = cv2.waitKey(1)
            if self.load != "" and not step_wise and key == ord('s'):
                step_wise = True
            if key == ord('q'):
                break
            if step_wise:
                while True:
                    key = cv2.waitKey(1)
                    if key == ord('s'):
                        break
                    elif key == ord('a'):
                        step_wise = False
                        break

        cv2.destroyAllWindows()

    def read_file(self, ch, frame_id):
        image_filename = f"image-{ch}-{frame_id:06d}"
        heatmap_filename = f"heatmap-{ch}-{frame_id:06d}"

        # 파일 경로 생성
        image_path = os.path.join(self.load, image_filename)
        heatmap_path = os.path.join(self.load, heatmap_filename)

        if not os.path.exists(image_path) or not os.path.exists(heatmap_path):
            print("No such file or directory")
            print(" - ", image_path)
            print(" - ", heatmap_path)
            return [None] * 104, [None] * 24

        image_array = np.fromfile(image_path, dtype='int8')
        heatmap_array  = np.fromfile(heatmap_path, dtype='int8')

        return image_array, heatmap_array

    def get_frame_id_range(self, load_folder, ch=0):
        # 정규 표현식을 사용하여 파일 이름에서 frame_id를 추출
        pattern = re.compile(rf'image-{ch}-(\d{{6}})')

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

    def visualize_skeleton(self, heatmap, image):
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

        keypoint_positions = []

        skeletons = np.zeros((11, 2))

        for i in range(NUM_KEYPOINTS):
            # 각 keypoint에 대해 DBSCAN 클러스터링
            points = np.argwhere(heatmap[:, :, i] > 0.3)
            if len(points) > 0:
                db = DBSCAN(eps=3, min_samples=2).fit(points)
                labels = db.labels_

                # 가장 큰 클러스터의 중심을 계산
                if len(labels) > 0 and np.any(labels >= 0):
                    largest_cluster = points[labels == np.argmax(np.bincount(labels[labels >= 0]))]
                    if len(largest_cluster) > 0:
                        # center_y, center_x = np.mean(largest_cluster, axis=0).astype(int)
                        max_y, max_x = largest_cluster[np.argmax(heatmap[largest_cluster[:, 0], largest_cluster[:, 1], i])]

                        # 중심 위치를 기록
                        keypoint_positions.append((i, max_x, max_y))

                        # 중심 위치에 원을 그림
                        center = (int(max_x * IMAGE_WIDTH / HEATMAP_WIDTH), int(max_y * IMAGE_HEIGHT / HEATMAP_HEIGHT))
                        self.keypoint_history[i].append(center)
                        # 이동 평균 적용
                        avg_x = int(np.mean([pos[0] for pos in self.keypoint_history[i]]))
                        avg_y = int(np.mean([pos[1] for pos in self.keypoint_history[i]]))
                        cv2.circle(image, (avg_x, avg_y), 3, colors[i], -1)
                        # cv2.putText(image, str(i), (avg_x + 5, avg_y + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, colors[i], 1, cv2.LINE_AA)
                        skeletons[i][0] = avg_x
                        skeletons[i][1] = avg_y

        for str_bone_id, dst_bone_id in BODY_BONES_POSE_11:
            str_bone_x, str_bone_y = skeletons[str_bone_id.value]
            dst_bone_x, dst_bone_y = skeletons[dst_bone_id.value]

            if all(coord > 0 for coord in [str_bone_x, str_bone_y, dst_bone_x, dst_bone_y]):
                cv2.line(image, (int(str_bone_x), int(str_bone_y)), (int(dst_bone_x), int(dst_bone_y)), (255, 255, 255), 1)

        return image, keypoint_positions

    def combine_channel_images(self, packet_data_image, packet_data_heatmap):
        images = []
        skeletons = []
        for ch in range(4):
            if any(packet_data_image[ch]):
                full_payload = b''.join([pkt for pkt in packet_data_image[ch] if pkt is not None])
                if len(full_payload) >= IMAGE_WIDTH * IMAGE_HEIGHT * 3:
                    image_array = np.frombuffer(full_payload[:IMAGE_WIDTH * IMAGE_HEIGHT * 3], dtype=np.uint8)
                    image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
                    images.append(image)

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

                            heatmap_image = self.visualize_heatmaps(heatmap, image)
                            heatmap_image, _ = self.visualize_skeleton(heatmap, heatmap_image)
                            skeletons.append(heatmap_image)
                        else:
                            skeletons.append(np.zeros_like(image))
                    else:
                        skeletons.append(np.zeros_like(image))
                else:
                    images.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))
                    skeletons.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))
            else:
                images.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))
                skeletons.append(np.zeros((IMAGE_HEIGHT, IMAGE_WIDTH, 3), dtype=np.uint8))

        # 이미지와 skeleton을 결합하여 그리드 형태로 표시
        combined_top_row = cv2.hconcat([images[0], skeletons[0], images[1], skeletons[1]])
        combined_bottom_row = cv2.hconcat([images[2], skeletons[2], images[3], skeletons[3]])
        combined_image = cv2.vconcat([combined_top_row, combined_bottom_row])
        combined_image = cv2.cvtColor(combined_image, cv2.COLOR_BGR2RGB)

        return combined_image

    def save_image_and_heatmap(self, folder, ch, frame_id, image_array, heatmap_array, heatmap_image):
        # 파일 이름 생성
        image_filename = f"image-{ch}-{frame_id:06d}.bin"
        heatmap_filename = f"heatmap-{ch}-{frame_id:06d}.bin"
        image_jpg_filename = f"image-{ch}-{frame_id:06d}.jpg"
        heatmap_jpg_filename = f"heatmap-{ch}-{frame_id:06d}.jpg"

        # 파일 경로 생성
        image_path = os.path.join(folder, image_filename)
        heatmap_path = os.path.join(folder, heatmap_filename)
        image_jpg_path = os.path.join(folder, image_jpg_filename)
        heatmap_jpg_path = os.path.join(folder, heatmap_jpg_filename)

        # 이미지 저장
        image_array.astype('int8').tofile(image_path)
        heatmap_array.astype('int8').tofile(heatmap_path)
        cv2.imwrite(image_jpg_path, image_array)
        cv2.imwrite(heatmap_jpg_path, heatmap_image)
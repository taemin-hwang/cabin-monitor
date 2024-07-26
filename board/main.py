import socket
import struct
import numpy as np
import cv2
from PIL import Image
import os
from sklearn.cluster import DBSCAN
from collections import deque
from datetime import datetime
import argparse

DEFAULT_PORT = 8888
DEFAULT_BUFLEN = 1460 * 2
IMAGE_WIDTH = 192
IMAGE_HEIGHT = 256
HEATMAP_WIDTH = 48
HEATMAP_HEIGHT = 64
NUM_KEYPOINTS = 11
MOVING_AVERAGE_WINDOW = 1  # 이동 평균 윈도우 크기

# 각 keypoint의 좌표를 저장할 큐
keypoint_history = {i: deque(maxlen=MOVING_AVERAGE_WINDOW) for i in range(NUM_KEYPOINTS)}

def process_packet(data, length):
    if length < 9:
        print("Error: length is less than 9")
        return None, None, None, None, None, None, None

    stx = data[0]
    length_field = int.from_bytes(data[1:3], "little")
    ch = data[3]
    count = data[4]
    payload_length = length_field - 7  # Subtract the header size (5 bytes: STX, LENGTH, CH, Count)
    payload = data[5:5+payload_length]

    csum = data[5+payload_length]
    etx = data[6+payload_length]

    if length < 7 + payload_length:  # Ensure the packet length matches
        print("Error: length is less then 7 + payload_length")
        return None, None, None, None, None, None, None

    return stx, length_field, ch, count, payload, csum, etx

def visualize_heatmaps(heatmap, image):
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

    blended_image = 0.6 * image.astype(np.float32) / 255.0 + 0.4 * overlay_image
    blended_image = np.clip(blended_image, 0, 1)

    return (blended_image * 255).astype(np.uint8)

def visualize_skeleton(heatmap, image):
    colors = [
        (0, 0, 255),    # Red
        (0, 255, 0),    # Green
        (255, 0, 0),    # Blue
        (0, 255, 255),  # Yellow
        (255, 0, 255),  # Magenta
        (255, 255, 0),  # Cyan
        (0, 128, 255),  # Orange
        (128, 0, 255),  # Purple
        (128, 255, 0),  # Lime
        (255, 128, 0),  # Sky Blue
        (128, 128, 0)   # Olive
    ]

    keypoint_positions = []

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
                    center_y, center_x = np.mean(largest_cluster, axis=0).astype(int)

                    # 중심 위치를 기록
                    keypoint_positions.append((i, center_x, center_y))

                    # 중심 위치에 원을 그림
                    center = (int(center_x * IMAGE_WIDTH / HEATMAP_WIDTH), int(center_y * IMAGE_HEIGHT / HEATMAP_HEIGHT))
                    keypoint_history[i].append(center)
                    # 이동 평균 적용
                    avg_x = int(np.mean([pos[0] for pos in keypoint_history[i]]))
                    avg_y = int(np.mean([pos[1] for pos in keypoint_history[i]]))
                    cv2.circle(image, (avg_x, avg_y), 5, colors[i], -1)

    return image, keypoint_positions

def create_log_folder():
    # 현재 날짜와 시간을 yymmddhhmmss 형식으로 가져옴
    current_time = datetime.now().strftime("%y%m%d%H%M%S")
    # 폴더 이름을 생성
    folder_name = f"log-{current_time}"

    # 폴더 생성
    os.makedirs(folder_name, exist_ok=True)
    print(f"Folder '{folder_name}' created successfully.")
    return folder_name

def save_image_and_heatmap(folder, ch, frame_id, image_array, heatmap_array, heatmap_image):
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

def read_from_device():
    # folder = create_log_folder()
    frame_id = 0

    ReceivingSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ReceiverAddr = ('', DEFAULT_PORT)

    ReceivingSocket.bind(ReceiverAddr)

    print(f"Server: Receiving on port {DEFAULT_PORT}")

    # 각 채널과 cnt 별로 패킷 데이터를 저장할 배열
    packet_data_image = {ch: [None] * 104 for ch in range(4)}
    packet_data_heatmap = {ch: [None] * 24 for ch in range(4)}
    heatmap = np.zeros((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS), dtype=np.uint8)

    cv2.namedWindow("Received Images", cv2.WINDOW_NORMAL)

    while True:
        ByteReceived, SenderAddr = ReceivingSocket.recvfrom(DEFAULT_BUFLEN)
        length = len(ByteReceived)

        stx, length_field, ch, count, payload, csum, etx = process_packet(ByteReceived, length)

        if stx is None or ch > 3:
            print("stx is None or ch > 3")
            print("ch : ", ch)
            continue

        if stx == 0x20:
            packet_data_image[ch][count] = payload

            if count == 103:  # End of image
                print(f"Received full image for channel {ch}")
                full_payload = b''.join([pkt for pkt in packet_data_image[ch] if pkt is not None])
                total_bytes = IMAGE_WIDTH * IMAGE_HEIGHT * 3

                if len(full_payload) >= total_bytes:
                    image_array = np.frombuffer(full_payload[:total_bytes], dtype=np.uint8)
                    image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    # 히트맵이 있는 경우 skeleton 생성
                    if any(packet_data_heatmap[ch]):
                        full_heatmap_payload = b''.join([pkt for pkt in packet_data_heatmap[ch] if pkt is not None])
                        if len(full_heatmap_payload) >= HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS:
                            heatmap_array = np.frombuffer(full_heatmap_payload[:HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS], dtype=np.uint8)
                            heatmap = heatmap_array.reshape((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS))
                            heatmap_image = visualize_heatmaps(heatmap, np.zeros_like(image))
                            heatmap_image, keypoint_positions = visualize_skeleton(heatmap, heatmap_image)
                        else:
                            heatmap_image = np.zeros_like(image)
                    else:
                        heatmap_image = np.zeros_like(image)

                    # 이미지 저장
                    # save_image_and_heatmap(folder, ch, frame_id, image, heatmap_array, heatmap_image)

                    frame_id += 1

                    # 전체 이미지를 결합하여 표시
                    combined_image = combine_channel_images(packet_data_image, packet_data_heatmap)
                    cv2.imshow("Received Images", combined_image)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
                else:
                    print(f"Error: Incomplete image data received for channel {ch}.")

                # packet_data_image[ch] = [None] * 104  # Reset for the next image

        elif stx == 0x02:
            packet_data_heatmap[ch][count] = payload
            if count == 23:  # End of heatmap
                print(f"Received full heatmap for channel {ch}")
                full_payload = b''.join([pkt for pkt in packet_data_heatmap[ch] if pkt is not None])
                total_bytes = HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS

                if len(full_payload) >= total_bytes:
                    heatmap_array = np.frombuffer(full_payload[:total_bytes], dtype=np.uint8)
                    heatmap = heatmap_array.reshape((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS))
                else:
                    print(f"Error: Incomplete heatmap data received for channel {ch}.")

                # packet_data_heatmap[ch] = [None] * 24  # Reset for the next heatmap

    cv2.destroyAllWindows()
    ReceivingSocket.close()

def combine_channel_images(packet_data_image, packet_data_heatmap):
    images = []
    skeletons = []
    for ch in range(4):
        if any(packet_data_image[ch]):
            full_payload = b''.join([pkt for pkt in packet_data_image[ch] if pkt is not None])
            if len(full_payload) >= IMAGE_WIDTH * IMAGE_HEIGHT * 3:
                image_array = np.frombuffer(full_payload[:IMAGE_WIDTH * IMAGE_HEIGHT * 3], dtype=np.uint8)
                image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
                image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                images.append(image)

                if any(packet_data_heatmap[ch]):
                    full_heatmap_payload = b''.join([pkt for pkt in packet_data_heatmap[ch] if pkt is not None])
                    if len(full_heatmap_payload) >= HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS:
                        heatmap_array = np.frombuffer(full_heatmap_payload[:HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS], dtype=np.uint8)
                        heatmap = heatmap_array.reshape((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS))
                        heatmap_image = visualize_heatmaps(heatmap, np.zeros_like(image))
                        heatmap_image, _ = visualize_skeleton(heatmap, heatmap_image)
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
    return combined_image

def main(load_dir):
    if load_dir:
        print("Reading from file is not implemented yet.")
        # read_from_file(load_dir)
    else:
        read_from_device()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some images and heatmaps.")
    parser.add_argument("--load", type=str, help="Directory to load logs from")
    args = parser.parse_args()
    main(args.load)

import socket
import struct
import numpy as np
import cv2
import copy
from PIL import Image
import os
import math
import numpy as np
from sklearn.cluster import DBSCAN
from collections import deque

DEFAULT_PORT = 8888
DEFAULT_BUFLEN = 1460 * 2
IMAGE_WIDTH = 192
IMAGE_HEIGHT = 256
HEATMAP_WIDTH = 48
HEATMAP_HEIGHT = 64
NUM_KEYPOINTS = 11
MOVING_AVERAGE_WINDOW = 5  # 이동 평균 윈도우 크기

# 각 keypoint의 좌표를 저장할 큐
keypoint_history = {i: deque(maxlen=MOVING_AVERAGE_WINDOW) for i in range(NUM_KEYPOINTS)}

def process_packet(data, length):
    if length < 9:
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
    print("heatmap shape : ", heatmap.shape)
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

    # for i in range(NUM_KEYPOINTS):
    #     # 각 keypoint에 대해 최대 값의 위치를 찾음
    #     _, max_val, _, max_loc = cv2.minMaxLoc(heatmap[:, :, i])

    #     print("[{}], {}".format(i, max_val))
    #     if max_val > 0.5:
    #         # 최대 값의 위치에 원을 그림
    #         center = (int(max_loc[0] * IMAGE_WIDTH / HEATMAP_WIDTH), int(max_loc[1] * IMAGE_HEIGHT / HEATMAP_HEIGHT))
    #         cv2.circle(image, center, 5, colors[i], -1)

    keypoint_positions = []

    for i in range(NUM_KEYPOINTS):
        # 각 keypoint에 대해 DBSCAN 클러스터링
        points = np.argwhere(heatmap[:, :, i] > 0.4)
        if len(points) > 0:
            db = DBSCAN(eps=3, min_samples=2).fit(points)
            labels = db.labels_

            # 가장 큰 클러스터의 중심을 계산
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


def main():
    ReceivingSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    ReceiverAddr = ('', DEFAULT_PORT)

    ReceivingSocket.bind(ReceiverAddr)

    print(f"Server: Receiving on port {DEFAULT_PORT}")

    packet_data_image = []  # Temporary storage for image packet data
    packet_data_heatmap = []  # Temporary storage for heatmap packet data
    heatmap = np.zeros((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS), dtype=np.uint8)

    cv2.namedWindow("Received Images", cv2.WINDOW_NORMAL)

    image_array = None
    heatmap_array = None

    while True:
        ByteReceived, SenderAddr = ReceivingSocket.recvfrom(DEFAULT_BUFLEN)
        length = len(ByteReceived)

        stx, length_field, ch, count, payload, csum, etx = process_packet(ByteReceived, length)

        if stx is None:
            continue

        if stx == 0x20:
            packet_data_image.append(payload)

            if count == 103:  # End of image
                print("Received full image")
                full_payload = b''.join(packet_data_image)
                total_bytes = IMAGE_WIDTH * IMAGE_HEIGHT * 3

                if len(full_payload) >= total_bytes:
                    image_array = np.frombuffer(full_payload[:total_bytes], dtype=np.uint8)

                    image = image_array.reshape((IMAGE_HEIGHT, IMAGE_WIDTH, 3))
                    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                    # Overlay the latest heatmap on the image
                    # blended_image = visualize_heatmaps(heatmap, np.zeros_like(image))
                    blended_image = visualize_heatmaps(heatmap, image)
                    blended_image, keypoint_positions = visualize_skeleton(heatmap, blended_image)

                    # Concatenate images horizontally
                    combined_image = np.hstack((image, blended_image))
                    combined_image = cv2.resize(combined_image, dsize=(0, 0), fx=4.0, fy=4.0)
                    cv2.imshow("Received Images", combined_image)
                    # cv2.imshow("Received Images", image)

                    # overlay_heatmaps(heatmap, base_image)

                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        image_array.astype('int8').tofile('image.dat')
                        heatmap_array.astype('int8').tofile('heatmap.dat')
                        break
                else:
                    print("Error: Incomplete image data received.")

                packet_data_image = []  # Reset for the next image

        elif stx == 0x02:
            packet_data_heatmap.append(payload)
            if count == 23:  # End of heatmap
                print("Received full heatmap")
                full_payload = b''.join(packet_data_heatmap)
                total_bytes = HEATMAP_WIDTH * HEATMAP_HEIGHT * NUM_KEYPOINTS

                if len(full_payload) >= total_bytes:
                    heatmap_array = np.frombuffer(full_payload[:total_bytes], dtype=np.uint8)
                    heatmap = np.zeros((HEATMAP_HEIGHT, HEATMAP_WIDTH, NUM_KEYPOINTS))
                    addr_file = os.path.join('./', 'out_addr.txt')

                    pos = 0
                    with open(addr_file, 'r') as fID_addr:
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
                else:
                    print("Error: Incomplete heatmap data received.")

                packet_data_heatmap = []  # Reset for the next heatmap

    cv2.destroyAllWindows()
    ReceivingSocket.close()

if __name__ == "__main__":
    main()

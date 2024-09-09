from transfer import transfer_interface

import struct
import numpy as np
import asyncio

class IviTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)

    def send_data(self, skeleton, control, status):
        if skeleton is None or control is None or status is None:
            print("skeleton or control or status is None")
            return

        skeleton_bytes = np.zeros((64, 48, 11), dtype=np.uint8)
        for i in range(11):
            keypoint_x = skeleton[i][0]
            keypoint_y = skeleton[i][1]

            keypoint_x /= 10 # 640 -> 64
            keypoint_y /= 10 # 480 -> 48
            skeleton_bytes[int(keypoint_x)][int(keypoint_y)][i] = 1

        packet = np.array(np.zeros(4), dtype=np.uint32)

        packet[0] = 0 # skeleton
        packet[1] = self.id
        packet[2] = int(status)
        packet[3] = int(control)

        packet = np.append(packet, skeleton_bytes.flatten())

        packed_packet = struct.pack('4i33792B', *packet)

        # print("packet size : ", len(packed_packet))

        self.send(packed_packet)

    def send_skeleton(self, skeleton):
        if skeleton is None:
            return

        packet = np.array(np.zeros(3 + 22), dtype=np.uint32)
        packet[0] = 1 # skeleton
        packet[1] = 92 # 22 * 4 + 4
        packet[2] = self.id

        for i in range(11):
            packet[3 + i * 2] = int(skeleton[i][0])
            packet[3 + i * 2 + 1] = int(skeleton[i][1])

        packed_packet = struct.pack('25i', *packet)

        self.send(packed_packet)

    def send_control(self, control):
        if control is None:
            return

        # create packet with 12 bytes
        packet = np.array(np.zeros(3), dtype=np.uint32)

        packet[0] = 4 # control
        packet[1] = 1
        packet[2] = int(control)

        # print data with hex
        # for i in range(packet.size):
        #     print(hex(packet[i]))

        packed_packet = struct.pack('3i', *packet)

        self.send(packed_packet)

    def send_status(self, status):
        if status is None:
            return

        # create packet with 12 bytes
        packet = np.array(np.zeros(3), dtype=np.uint32)

        packet[0] = 3 # status
        packet[1] = 1
        packet[2] = int(status)

        packed_packet = struct.pack('3i', *packet)

        self.send(packed_packet)
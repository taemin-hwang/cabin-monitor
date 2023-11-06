from transfer import transfer_interface

import numpy as np

class IviTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)

    def send_skeleton(self, skeleton):
        if skeleton is None:
            return

        skeleton = np.array(skeleton)

        packet = np.array(np.zeros(3 + 11), dtype=np.float32)
        packet[0] = 1 # skeleton
        packet[1] = 11
        packet[2] = self.id

        self.send(skeleton)

    def send_control(self, control):
        if control is None:
            return

        # create packet with 12 bytes
        packet = np.array(np.zeros(3), dtype=np.uint32)

        packet[0] = 4 # control
        packet[1] = 1
        packet[2] = control

        self.send(control)

    def send_status(self, status):
        if status is None:
            return

        # create packet with 12 bytes
        packet = np.array(np.zeros(3), dtype=np.uint32)

        packet[0] = 3 # status
        packet[1] = 1
        packet[2] = status

        self.send(status)
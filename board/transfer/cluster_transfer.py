from transfer import transfer_interface

import numpy as np
import json
class ClusterTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)
        self.handler = None

    def set_recv_handler(self, f):
        self.handler = f

    def recv_data(self):
        print("Recv data from : ", self.ip, ":", self.port)
        while True:
            data, addr = self.socket.recvfrom(1024)
            print("recv data : ", data)
            if data == b'stt':
                voice = self.handler()
                self.send_voice(voice)

    def send_voice(self, voice):
        if voice is None:
            return

        json_data = {
            'id': self.id,
            'type' : 1, # voice
            'voice': voice
        }

        json_string = json.dumps(json_data)
        print(json_string)
        self.send(json_string.encode())

    def send_data(self, ch, skeleton, control, status, gaze):
        # {
        #   id : 1,
        #   status : 1,
        #   control : 1,
        #   skeleton : [
        #       [1, 2],
        #       [3, 4],
        #       ...
        #   ]
        # }

        # Round to the 4th decimal place
        skeleton = np.round(skeleton, 4)

        json_data = {
            'id': ch,
            'type' : 0, # skeleton
            'status': status,
            'control': control,
            'gaze': gaze,
            'skeleton': skeleton.tolist()
        }

        json_string = json.dumps(json_data)

        # print(json_string)

        self.send(json_string.encode())

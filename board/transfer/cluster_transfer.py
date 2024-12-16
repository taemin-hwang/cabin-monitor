import os
from datetime import datetime
from transfer import transfer_interface

import numpy as np
import json

class ClusterTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)
        self.handler = None

        # Output directory path
        self.output_dir = None
        self.file_counter = 0

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

    def _ensure_output_dir(self):
        # Create a folder in ./out/ with the current timestamp (YY-MM-dd_HH-MM-ss)
        if self.output_dir is None:
            timestamp = datetime.now().strftime('%y-%m-%d_%H-%M-%S')
            self.output_dir = os.path.join('./out', timestamp)
            os.makedirs(self.output_dir, exist_ok=True)

    def _save_json_to_file(self, json_string):
        # Ensure the output directory exists
        self._ensure_output_dir()

        # Increment file counter
        self.file_counter += 1
        filename = f"{self.file_counter:06d}.json"
        file_path = os.path.join(self.output_dir, filename)

        # Save JSON string to file
        with open(file_path, 'w') as json_file:
            json_file.write(json_string)
        # print(f"Saved JSON to {file_path}")

    def send_data(self, ch, skeleton, control, status, gaze):
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

        # Save JSON string to file
        self._save_json_to_file(json_string)

        # Send JSON string
        self.send(json_string.encode())

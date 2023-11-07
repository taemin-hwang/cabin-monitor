from transfer.cluster_transfer import ClusterTransfer
from transfer.ivi_transfer import IviTransfer

import json
import threading

class TransferManager:
    def __init__(self):
        # read json from ../etc/config.json
        with open('./etc/config.json') as json_file:
            json_data = json.load(json_file)
            self.id = json_data['id']
            self.cluster_ip = json_data['cluster ip']
            self.cluster_port = json_data['cluster port']
            self.ivi_ip = json_data['workpad ip']
            self.ivi_port = json_data['workpad port']

        self.cluster_transfer = ClusterTransfer(self.id, self.cluster_ip, self.cluster_port)
        self.ivi_transfer = IviTransfer(self.id, self.ivi_ip, self.ivi_port)

    def init(self):
        t1 = threading.Thread(target=self.cluster_transfer.recv_data).start()

    def set_recv_handler(self, f):
        self.cluster_transfer.set_recv_handler(f)

    def run(self, skeleton, control, status):
        self.cluster_transfer.send_data(skeleton, control, status)
        self.ivi_transfer.send_data(skeleton, control, status)
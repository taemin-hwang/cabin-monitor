from transfer import transfer_interface

import numpy as np
import json
class ClusterTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)

    def send_data(self, skeleton, control, status):
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
            'id': self.id,
            'status': status,
            'control': control,
            'skeleton': skeleton.tolist()
        }

        json_string = json.dumps(json_data)

        # print(json_string)

        self.send(json_string.encode())

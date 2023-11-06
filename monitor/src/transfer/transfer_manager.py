from transfer.cluster_transfer import ClusterTransfer
from transfer.ivi_transfer import IviTransfer

class TransferManager:
    def __init__(self):
        self.cluster_transfer = ClusterTransfer(1, '127.0.0.1', 5000)
        self.ivi_transfer = IviTransfer(1, '127.0.0.1', 5001)

    def run(self, skeleton, control, status):
        self.cluster_transfer.send_skeleton(skeleton)
        self.cluster_transfer.send_control(control)
        self.cluster_transfer.send_status(status)

        self.ivi_transfer.send_skeleton(skeleton)
        self.ivi_transfer.send_control(control)
        self.ivi_transfer.send_status(status)
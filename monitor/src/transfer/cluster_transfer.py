from transfer import transfer_interface

class ClusterTransfer(transfer_interface.TransferInterface):
    def __init__(self, id, ip, port):
        super().__init__(id, ip, port)

    def send_skeleton(self, skeleton):
        self.send(skeleton)

    def send_control(self, control):
        self.send(control)

    def send_status(self, status):
        self.send(status)
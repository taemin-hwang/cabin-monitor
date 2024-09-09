import socket

class TransferInterface:
    def __init__(self, id, ip, port):
        self.id = id
        self.ip = ip
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def send(self, data):
        if data is None:
            return
        self.socket.sendto(data, (self.ip, self.port))
import socket
from utils import *

class TransferManager:
    def __init__(self, port=DEFAULT_PORT):
        self.recv_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        recv_addr = ('', port)
        self.recv_socket.bind(recv_addr)
        print(f"Server: Receiving on port {port}")

    def init(sef):
        pass

    def run(self):
        pass

    def shutdown(self):
        self.recv_socket.close()

    def get_data(self):
        byte_recv, sender_addr = self.recv_socket.recvfrom(DEFAULT_BUFLEN)
        length = len(byte_recv)

        stx, length_field, ch, count, payload, csum, etx = self.process_packet(byte_recv, length)
        return stx, length_field, ch, count, payload, csum, etx

    def process_packet(self, data, length):
        if length < 9:
            print("Error: length is less than 9")
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
            print("Error: length is less then 7 + payload_length")
            return None, None, None, None, None, None, None

        return stx, length_field, ch, count, payload, csum, etx
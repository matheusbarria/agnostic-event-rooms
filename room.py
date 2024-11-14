import socket
import logging
import multiprocessing


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class Room(multiprocessing.Process):
    def __init__(self, join_code, client_socket, app_server_addr):
        super().__init__()
        self.join_code = join_code
        self.client_sockets = {client_socket.fileno(): client_socket}
        self.app_server_addr = app_server_addr
        # self.sel = selectors.DefaultSelector()
        self.app_socket = None
    
    def run(self):
        logging.info(f"Room {self.join_code} should now try to connect to gameserver.")
        self.send_to_clients(f"<html><body>Room {self.join_code}</body></html>".encode())
        return

    def send_to_clients(self, message):
        for client_num, sock in self.client_sockets.items():
            sock.sendall(message)
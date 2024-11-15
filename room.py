import select
import socket
import logging
import multiprocessing
import struct

class Room(multiprocessing.Process):
    def __init__(self, join_code, client_socket, app_server_addr):
        super().__init__()
        self.join_code = join_code
        self.client_sockets = {client_socket.fileno(): client_socket}
        self.app_server_addr = app_server_addr
        self.app_socket = None

    def connect_to_game_server(self):
        self.app_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.app_socket.connect(self.app_server_addr)
            return True
        except Exception as e:
            logging.error(f"Failed to connect to game server: {e}")
            return False

    def receive_message(self, sock):
        try:
            length_bytes = sock.recv(4)
            if not length_bytes:
                return None
            length = struct.unpack('!I', length_bytes)[0]
            data = sock.recv(length)
            return data
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    def send_message(self, sock, data):
        try:
            length = len(data)
            sock.sendall(struct.pack('!I', length))
            sock.sendall(data)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def run(self):
        logging.info(f"Room {self.join_code} connecting to game server.")
        
        if not self.connect_to_game_server():
            self.send_to_all_clients(b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to connect to game server")
            return

        initial_response = self.receive_message(self.app_socket)
        if initial_response:
            self.send_to_all_clients(initial_response)

        while True:
            readable, _, _ = select.select(list(self.client_sockets.values()) + [self.app_socket], [], [], 0.1)
            
            for sock in readable:
                if sock == self.app_socket:
                    # Message from game server
                    data = self.receive_message(sock)
                    if data:
                        self.send_to_all_clients(data)
                    else:
                        logging.info("Game server disconnected")
                        return
                else:
                    # Message from client
                    data = sock.recv(1024)
                    if data:
                        self.send_message(self.app_socket, data)
                    else:
                        # Client disconnected
                        self.client_sockets.pop(sock.fileno(), None)
                        if not self.client_sockets:
                            logging.info("All clients disconnected")
                            return

    def send_to_all_clients(self, message):
        for client_num, sock in self.client_sockets.items():
            try:
                sock.sendall(message)
            except Exception as e:
                logging.error(f"Error sending to client {client_num}: {e}")
                self.client_sockets.pop(client_num, None)
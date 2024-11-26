import select
import socket
import logging
import threading
import json

class Room(threading.Thread):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    def __init__(self, join_code, client_socket, app_server_addr):
        super().__init__()
        self.join_code = join_code
        self.client_sockets = {client_socket.fileno(): client_socket}
        self.app_server_addr = app_server_addr
        self.app_socket = None
        self.running = True

    def connect_to_game_server(self):
        self.app_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.app_socket.connect(self.app_server_addr)
            self.app_socket.send(len(self.join_code.to_bytes(4,'big')).to_bytes(4,'big') + self.join_code.to_bytes(4,'big'))
            return True
        except Exception as e:
            logging.error(f"Failed to connect to game server: {e}")
            return False

    def receive_message(self, sock):
        try:
            bytes_data = sock.recv(4)
            if not bytes_data:
                return None
            length = int.from_bytes(bytes_data, byteorder='big')
            data = sock.recv(length)
            logging.info(f"Received message: {data}")
            return data
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    def send_to_app(self, data):
        try:
            if isinstance(data, dict):
                data = json.dumps(data)
            data = data.encode()
            resp = len(data).to_bytes(4, 'big') + data
            self.app_socket.sendall(resp)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def run(self):
        logging.info(f"Room {self.join_code} connecting to game server.")
        if not self.connect_to_game_server():
            self.send_to_all_clients(b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to connect to game server")
            return

        initial_response = self.receive_message(self.app_socket)
        if initial_response:
            print(type(initial_response))
            self.send_to_all_clients(initial_response)

        while self.running:
            readable, _, _ = select.select(list(self.client_sockets.values()) + [self.app_socket], [], [], 0.1)

            for sock in readable:
                if sock == self.app_socket:
                    # Message from game server
                    data = self.receive_message(sock)
                    # print('response from game server: ',data)
                    if data:
                        self.send_to_all_clients(data)
                    # else:
                    #     logging.info("Game server disconnected")
                    #     self.running = False
                    #     break
                else:
                    # Message from client
                    data = sock.recv(1024)
                    if data:
                        logging.info(f"Data from client: {data}")
                        self.send_to_app({'username': 'username', 'message': data.decode()})
                    else:
                        # Client disconnected
                        self.client_sockets.pop(sock.fileno(), None)
                        if not self.client_sockets:
                            logging.info("All clients disconnected")
                            self.running = False
                            break

    def send_to_all_clients(self, message):
        for client_num, sock in list(self.client_sockets.items()):
            try:
                sock.sendall(message)
                print('sending to clients from room')
                print(client_num, sock, message)
            except Exception as e:
                logging.error(f"Error sending to client {client_num}: {e}")
                self.client_sockets.pop(client_num, None)

    def get_response_from_parent(self, message):
        # print(f"Room recieved from parent: {message}")
        message = {"message":message, "user":0}
        self.send_to_app(message)

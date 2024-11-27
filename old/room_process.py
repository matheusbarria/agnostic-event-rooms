import select
import socket
import logging
import multiprocessing
import json
from ColorPrint import color_print

class Room(multiprocessing.Process):
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

    def __init__(self, join_code, port, app_server_addr):
        super().__init__()
        self.join_code = join_code
        # self.client_sockets = {client_socket.fileno(): client_socket}
        self.client_sockets = dict()
        self.app_server_addr = app_server_addr
        self.app_socket = None
        self.host = '127.0.0.1'
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        self.location = self.server_socket.getsockname()
        print(f'Room {self.join_code} listening on port {self.location}')
        self.latest_page = b"" # Cache last page recieved

    def connect_to_game_server(self):
        self.app_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.app_socket.connect(self.app_server_addr)
            self.app_socket.send(len(self.join_code.to_bytes(4,'big')).to_bytes(4,'big') + self.join_code.to_bytes(4,'big'))
            logging.error(f"Connected to game server: {self.app_socket}")
            return True
        except Exception as e:
            logging.error(f"Failed to connect to game server: {e}")
            return False

    def receive_message(self, sock):
        try:
            bytes = sock.recv(4)
            length = int.from_bytes(bytes, byteorder='big')
            if not length:
                return None
            data = sock.recv(length)
            print(f'recieved message from app: {data}')
            return data
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            return None

    def send_to_app(self, data):
        try:
            if type(data)==dict:
                data = json.dumps(data)
            data = data.encode()
            resp = len(data).to_bytes(4,'big') + data
            self.app_socket.sendall(resp)
        except Exception as e:
            logging.error(f"Error sending message: {e}")

    def run(self):
        # TODO: create new socket binding to wait for clients

        logging.info(f"Room {self.join_code} connecting to game server.")
        if not self.connect_to_game_server():
            self.send_to_all_clients(b"HTTP/1.1 500 Internal Server Error\r\n\r\nFailed to connect to game server")
            return
        initial_response = self.receive_message(self.app_socket)
        print('\ninitial resp:', initial_response)
        self.latest_page = initial_response
        if initial_response:
            self.send_to_all_clients(initial_response)
            print("\nroom connected to game server\n")

        while True:
            try:
                self.server_socket.listen(2) # play with this val
                sock, client_address = self.server_socket.accept()
                color_print(f"accepted connection from {client_address}", 'green')
                self.client_sockets[sock.fileno()] = sock
                data = sock.recv(1024)
                resp = self.handle_http_request(data)
                self.send_to_all_clients(resp)
            except Exception as ex:
                print(ex)

            readable, _, _ = select.select(list(self.client_sockets.values()) + [self.app_socket], [], [], 0.1)
            
            for sock in readable:
                if sock == self.app_socket:
                    # Message from game server
                    data = self.receive_message(sock)
                    self.latest_page = data
                    if data:
                        self.send_to_all_clients(data)
                    else:
                        logging.info("Game server disconnected")
                        return
                else:
                    # Message from client
                    data = sock.recv(1024)
                    if data:
                        print(f'data from client: {data}')
                        resp = self.handle_http_request(data)
                        self.send_to_app({'username':'username', 'message':data.get('message')})
                        self.send_to_all_clients(resp)
                    else:
                        # Client disconnected
                        self.client_sockets.pop(sock.fileno(), None)
                        if not self.client_sockets:
                            logging.info("All clients disconnected")
                            # return
    
    def handle_http_request(self,request_bytes):
        if not request_bytes:
            return b"No Content"
        request_str = request_bytes.decode()
        request_lines = request_str.split('\r\n')
        request_line = request_lines[0].split(' ')
        method = request_line[0]
        path = request_line[1]
        # Log the request details
        print(f"Room recieving: Method: {method}, Path: {path}")

        if method == 'GET':
            return self.latest_page
        elif method == 'POST':
            return self._handle_post(path,request_str)
        else:
            return b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>"

    def _handle_post(self,path, request):
        body = request.split('\r\n\r\n')[1]
        params = body.split('&')
        data = {k: v for k, v in (param.split('=') for param in params)}
        if path == f'/{self.join_code}':
            message = data.get('message')
            self.send_to_app({'message':message, 'username':'username'})
            return b"<h1>Sent to App Server</h1>"
        else:
            return b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Bad Request</h1></body></html>"

    def send_to_all_clients(self, message):
        for client_num, sock in self.client_sockets.items():
            try:
                print(f"\nsending to client {client_num}{sock}: {message}")
                sock.sendall(message)
            except Exception as e:
                logging.error(f"Error sending to client {client_num}: {e}")
                self.client_sockets.pop(client_num, None)
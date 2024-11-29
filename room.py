import socket, select
import logging
import json
from ColorPrint import color_print

class Room:
    def __init__(self, host, port, app_server_addr, join_code):
        self.host = host
        self.port = port
        self.join_code = join_code
        self.web_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # self.web_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.app_server_addr = app_server_addr
        self.app_socket = None
        self.latest_page = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Response</title>
</head>
<body>
    <h1>Welcome!</h1>
    <p>You have successfully reached the room server. Please reload the page.</p>
</body>
</html>
""".encode('utf-8')
        
    def local_error(self,message):
        color_print(message,"red")
        
    def connect_to_app(self):
        if self.app_socket:
            self.app_socket.close()
        self.app_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.app_socket.connect(self.app_server_addr)
            # self.app_socket.settimeout(0.1)
            self.app_socket.send(len(self.join_code.to_bytes(4,'big')).to_bytes(4,'big') + self.join_code.to_bytes(4,'big'))
            color_print(f"Connected to game server", 'green')
            return True
        except Exception as e:
            self.local_error(f"Failed to connect to game server: {e}")
            return False
        

    def start(self):
        try:
            # Bind and listen for connections
            self.web_socket.bind((self.host, self.port))
            self.web_socket.listen(10)
            self.web_socket.settimeout(1.0)
            print(f"Room listening on {self.host}:{self.port}")

            # Create TCP connection with application server
            self.connect_to_app()

            while True:
                try:
                    client_socket, client_address = self.web_socket.accept()
                    if client_address and client_socket:
                        self.handle_web_request(client_socket)
                except socket.timeout:
                    try:
                        readable, _, _ = select.select([self.app_socket], [], [], 0.5)
                        for sock in readable:
                            data = self.receive_message(sock)
                            if data:
                                self.latest_page = data
                            else:
                                logging.info("No data from game server")
                                self.local_error("No data from game server... will try to reconnect")
                                if not self.connect_to_app():
                                    self.latest_page = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Response</title>
</head>
<body>
    <h1>Connection to Application Server Failed!</h1>
</body>
</html>
""".encode('utf-8')

                    except socket.error as ex:
                        self.local_error(f"socket error recieving from application: {ex}")
                    except Exception as ex:
                        self.local_error(f"error recieving from application: {ex}")
                except socket.error as ex:
                    self.local_error(f"socket error recieving from application: {ex}")
                except Exception as ex:
                    self.local_error(f"error recieving from web client: {ex}")
        finally:
            self.web_socket.close()
            self.app_socket.close()
            print("Sockets closed.")
    
    def handle_web_request(self, client_socket):
        try:
            request_bytes = client_socket.recv(1024)
            if not request_bytes:
                return b"No Content"
            request_str = request_bytes.decode('utf-8')
            request_lines = request_str.split('\r\n')
            request_line = request_lines[0].split(' ')
            method = request_line[0]
            path = request_line[1]
            color_print(f'{method} {path}', 'cyan')
            logging.info(f"{method} {path}")
            if method == 'GET':
                client_socket.send(self.latest_page)
                client_socket.close()
            elif method == 'POST':
                body = request_str.split('\r\n\r\n')[1]
                params = body.split('&')
                data = {k: v for k, v in (param.split('=') for param in params)}
                message = data.get('message')
                client = data.get('client')
                self.send_to_app({'client':client, 'message':message, 'room':self.join_code})
                if self.app_socket:
                    data = self.receive_message(self.app_socket)
                    if data:
                        self.latest_page = data
                client_socket.send(self.latest_page)
                client_socket.close()
            else:
                # TODO: return error message
                client_socket.close()
        except socket.error as ex:
            self.local_error(f"socket error recieving from web: {ex}")
        except Exception as ex:
            self.local_error(f"error handling web request {ex}")
            client_socket.close()
        finally:
            client_socket.close()

    def receive_message(self, sock):
        try:
            raw_bytes = sock.recv(4)
            length = int.from_bytes(raw_bytes, byteorder='big')
            if not length:
                return None
            data = sock.recv(length)
            return data
        except Exception as e:
            logging.error(f"Error receiving message: {e}")
            self.local_error(f"Error receiving message: {e}")
            return None

    def send_to_app(self, data):
        try:
            if type(data)==dict:
                data = json.dumps(data)
            data = data.encode()
            resp = len(data).to_bytes(4,'big') + data
            self.app_socket.send(resp)
        except Exception as e:
            logging.error(f"Error sending message: {e}")
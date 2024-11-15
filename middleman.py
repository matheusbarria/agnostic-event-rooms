import socket
import logging
from room import Room
import json
import threading, time


# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')


class MiddlemanServer:
    application_servers_enum = []
    application_servers = {}  # Format: {'service_name': ('ip', port)}
    rooms = {}  # Format: {'join_code': Room}

    def __init__(self, host='127.0.0.1', port=5000, max_threads=10):
        self.host = host
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((self.host, self.port))
        # self.server_socket.bind((socket.gethostname(), port))
        # self.server_socket.listen()
        self.location = self.server_socket.getsockname()
        # self.executor = ThreadPoolExecutor(max_workers=max_threads)
        logging.info(f"Middleman server started on {self.host}:{self.port}")
        print(f'Listening on port {self.location}')
        self.join_code = 0
        self.rooms = {}


    def handle_http_request(self,request_bytes, sock):
        request_str = request_bytes.decode()
        request_lines = request_str.split('\r\n')
        request_line = request_lines[0].split(' ')
        method = request_line[0]
        path = request_line[1]
        # Log the request details
        print(f"Method: {method}, Path: {path}")

        if method == 'GET':
            return self._handle_get(path)
        elif method == 'POST':
            return self._handle_post(path,request_str, sock)
        else:
            return b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>"
    
    def _handle_get(self, path):
        if path == '/': # client requesting the index page
            html_content = '''
            <html>
            <head><title>Event Rooms</title></head>
            <body style="text-align: center;">
            <h1>Event Rooms!</h1>
            <br/>
            <h3>Select an Application to Create a Room:</h3>
            <ol style="list-style-position: inside; text-align: center;"> {application_servers} </ol>
            <br/>
            <form method="POST" action="/">
                <label for="server_number">Enter Application Number:\n</label>
                <input type="text" id="server_number" name="server_number" required> <input type="submit" value="Submit">
            </form>
            </body>
            </html> '''
            application_servers_list = ''.join(f'<li>{server}</li>' for server in self.application_servers_enum)
            html_content = html_content.format(application_servers=application_servers_list)
            return b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + html_content.encode()
        else:
            return b"HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<html><body><h1>404 Not Found</h1></body></html>"
        
    def _handle_post(self,path, request, sock):
        if path == '/': # client should be requesting an new application server room
            body = request.split('\r\n\r\n')[1]
            params = body.split('&')
            data = {k: v for k, v in (param.split('=') for param in params)}
            server_number = data.get('server_number')
            if server_number:
                try:
                    server_number = int(server_number) -  1
                except ValueError as ex:
                    print('invalid server number, room could not be created')
                    return b"HTTP/1.1 415 Unsupported Media\r\nContent-Type: text/html\r\n\r\n<html><body><h1>415 Unsupported Media</h1>Please enter an Integer</body></html>"
                if not self.is_natural_number(server_number) or server_number>=len(self.application_servers):
                    print('invalid server number, room could not be created')
                    return b"HTTP/1.1 415 Unsupported Media\r\nContent-Type: text/html\r\n\r\n<html><body><h1>415 Unsupported Media</h1>Please enter a valid application number</body></html>"
                self.create_room(sock, server_number)
                response_content = f'<html><body><h1>Received Server Number: {server_number}</h1></body></html>'
                return b"HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n" + response_content.encode()
            else: 
                return b"HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n<html><body><h1>Bad Request</h1></body></html>"

    def accept_connections(self):
        # create thread to accept registration requests
        name_thread = threading.Thread(target=self.register_application_server)
        name_thread.daemon = True
        name_thread.start()
        while True:
            try:
                self.server_socket.listen(2) # play with this val
                sock, client_address = self.server_socket.accept()
                try:
                    data = sock.recv(1024)
                except Exception as ex:
                    print(ex)
                resp = self.handle_http_request(data, sock)
                sock.sendall(resp)
            except Exception as ex:
                print(ex)
                continue
    
    def register_application_server(self):
        # UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 5001))
        while 1:
            data = sock.recv(1024)
            if data:
                data = json.loads(data)
                print(f'registration attempt: {data}')
                if data['service_name'] not in self.application_servers:
                    self.application_servers[data['service_name']] = (data['host'],data['port'])
                    self.application_servers_enum.append(data['service_name'])
        # logging.info(f"Registered application server {service_name} at {address}")

    def create_room(self, client_socket, server_number):
        app_server_location = self.application_servers.get(self.application_servers_enum[server_number])
        if app_server_location:
            # Start new room process
            room = Room(self.join_code, client_socket, app_server_location)
            self.rooms[self.join_code] = room
            room.start()
            logging.info(f"Room {self.join_code} created for service {self.application_servers_enum[server_number]}.")
            self.join_code+=1
        else:
            print('no app server location found; room could not be created')
            pass

    def is_natural_number(self,num):
        if type(num)!=int:
            return False
        if num < 0:
            return False
        return True

if __name__ == '__main__':

    middleman_server = MiddlemanServer()

    # # Register available application servers
    # middleman_server.register_application_server('trivia', ('127.0.0.1', 6000))
    # middleman_server.register_application_server('battleship', ('127.0.0.1', 6001))

    # Start accepting connections from clients
    middleman_server.accept_connections()
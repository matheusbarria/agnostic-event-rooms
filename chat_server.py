import socket, select
import json
from ColorPrint import color_print
from chat_html import html_page

MIDDLEMAN_ADDRESS = ('127.0.0.1',5001)
APPLICATION_NAME = 'chat'
# APPLICATION_HOST = '127.0.0.2'

def registration_message(host,port):
    message = {
        "service_name" : APPLICATION_NAME,
        "host" : host,
        "port" : port,
    }
    return message

def receive(sock):
    raw_msglen = _receive_all(sock, 4)
    if not raw_msglen:
        return None
    print(raw_msglen)
    # msglen = struct.unpack('>I', raw_msglen)[0]
    return _receive_all(sock,raw_msglen)

def _receive_all(sock, n):
    resp = bytearray()
    while len(resp) < n:
        data = sock.recv(n - len(resp))
        if not data:
            return None
        resp.extend(data)
    return resp

def format_response(html,message_list):
    messages = ''.join(f'<div class="chat-message"><div class="message-sender">{user}:</div><div class="message-text">{text}</div></div>' for user,text in message_list)
    page = html.format(messages=messages)
    return page

sockets_list = {} # socket : chat_history

# create a TCP socket to listen for new rooms
port = 0
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
server_socket.bind((host,port))
port = server_socket.getsockname()
sockets_list[server_socket] = server_socket.fileno() # master socket
server_socket.listen(2)

# Register with Middleman Server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(registration_message(host,port)).encode(), MIDDLEMAN_ADDRESS)
sock.close()

while True:
        readable, _, _ = select.select(sockets_list.keys(), [], [], 0)
        for sock in readable:
            if sock == server_socket:
                connection, client_address = sock.accept()
                sockets_list[connection] = []
                color_print(f'New connection from {sockets_list[connection]} (socket {connection.fileno()})', 'green')
            else:
                try:
                    data = b""
                    data = receive(sock)
                    if data:
                        print(data)
                        demarshalled = json.loads(data)
                        if type(demarshalled) != dict:
                            raise ValueError
                        if 'message' not in demarshalled or 'user' not in demarshalled:
                            raise KeyError
                        sockets_list[sock].append((demarshalled['user'],demarshalled['message']))
                        response = json.dumps(format_response(html=html_page, message_list=sockets_list[sock][-10:]))
                        response = len(response).to_bytes(4) + response
                        sock.sendall(response)
                         
                except ConnectionResetError:
                    print(f'Connection terminated from socket {sock.fileno()}')
                    sockets_list.pop(sock)
                except Exception as ex:
                    print(ex)
                finally:
                    try:
                        sockets_list.pop(sock)
                        sock.close()
                    except Exception as ex:
                        print(ex)
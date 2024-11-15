import socket, select
import json
from ColorPrint import color_print
# from chat_html import html_page

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

html_page = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Chat Room</title><style>body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; } .chat-container { width: 50%; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border-radius: 8px; overflow: hidden; } .chat-header { padding: 10px; background: #007bff; color: white; text-align: center; font-size: 1.2em; } .chat-messages { padding: 20px; height: 300px; overflow-y: scroll; border-bottom: 1px solid #ddd; } .chat-message { padding: 10px; border-radius: 4px; margin-bottom: 10px; } .message-sender { font-weight: bold; margin-bottom: 5px; } .message-text { margin: 0; } .chat-input { display: flex; padding: 10px; } .chat-input input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; outline: none; } .chat-input button { padding: 10px 20px; border: 1px solid #007bff; background: #007bff; color: white; border-radius: 0 4px 4px 0; cursor: pointer; } .chat-input button:hover { background: #0056b3; } </style></head><body><div class="chat-container"><div class="chat-header">Chat Room</div><div class="chat-messages">{messages}</div><div class="chat-input"><input type="text" placeholder="Type your message..."><button>Send</button></div></div></body></html>'
def format_response(html,message_list):
    messages = ''.join(f'<div class="chat-message"><div class="message-sender">{user}:</div><div class="message-text">{text}</div></div>' for user,text in message_list)
    # page = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Chat Room</title><style>body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; } .chat-container { width: 50%; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border-radius: 8px; overflow: hidden; } .chat-header { padding: 10px; background: #007bff; color: white; text-align: center; font-size: 1.2em; } .chat-messages { padding: 20px; height: 300px; overflow-y: scroll; border-bottom: 1px solid #ddd; } .chat-message { padding: 10px; border-radius: 4px; margin-bottom: 10px; } .message-sender { font-weight: bold; margin-bottom: 5px; } .message-text { margin: 0; } .chat-input { display: flex; padding: 10px; } .chat-input input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; outline: none; } .chat-input button { padding: 10px 20px; border: 1px solid #007bff; background: #007bff; color: white; border-radius: 0 4px 4px 0; cursor: pointer; } .chat-input button:hover { background: #0056b3; } </style></head><body><div class="chat-container"><div class="chat-header">Chat Room</div><div class="chat-messages">' + messages + '</div><div class="chat-input"><input type="text" placeholder="Type your message..."><button>Send</button></div></div></body></html>'
    page = '<!DOCTYPE html><html lang=en><head><meta charset=UTF-8><meta name=viewport content=width=device-width, initial-scale=1.0><title>Chat Room</title><style>body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; } .chat-container { width: 50%; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border-radius: 8px; overflow: hidden; } .chat-header { padding: 10px; background: #007bff; color: white; text-align: center; font-size: 1.2em; } .chat-messages { padding: 20px; height: 300px; overflow-y: scroll; border-bottom: 1px solid #ddd; } .chat-message { padding: 10px; border-radius: 4px; margin-bottom: 10px; } .message-sender { font-weight: bold; margin-bottom: 5px; } .message-text { margin: 0; } .chat-input { display: flex; padding: 10px; } .chat-input input[type=text] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; outline: none; } .chat-input button { padding: 10px 20px; border: 1px solid #007bff; background: #007bff; color: white; border-radius: 0 4px 4px 0; cursor: pointer; } .chat-input button:hover { background: #0056b3; } </style></head><body><div class=chat-container><div class=chat-header>Chat Room</div><div class=chat-messages>' + messages + '</div><div class=chat-input><form method=POST action=/><input type=text name=message placeholder=Type your message...><button type=submit>Send</button></form></div></div></body></html>'
    # page = '<body style=text-align: center;><form method=POST action=/><label for=message>Enter Message:</label><input type=text id=message name=message required> <input type=submit value=Submit></form></body>'
    # page = html.format(messages=messages)
    return page

sockets_list = {} # socket : chat_history

# create a TCP socket to listen for new rooms
port = 0
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
server_socket.bind((host,port))
port = server_socket.getsockname()[1]
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
                initial_response = json.dumps(format_response(html=html_page, message_list=[]))
                initial_response = len(initial_response).to_bytes(4,'big') + initial_response.encode()
                connection.sendall(initial_response)
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
                        response = len(response).to_bytes(4, 'big') + response.encode()
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

                
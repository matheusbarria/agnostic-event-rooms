import socket, select
import json
from ColorPrint import color_print
# from chat_html import html_page

MIDDLEMAN_ADDRESS = ('127.0.0.1',4999)
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
    raw_msglen = int.from_bytes(raw_msglen,'big')
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
    print("message list: ",message_list)
    # Construct chat messages HTML
    messages = ''.join(
        f'<div class="chat-message">'
        f'<div class="message-sender">{user}:</div>'
        f'<div class="message-text">{text}</div>'
        f'</div>'
        for user, text in message_list
    )
    print(messages)

# Construct the complete chat room page HTML
    page = f'''\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Room</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }}
        .flex {{
            display: flex;
        }}
        .chat-container {{
            width: 50%;
            background: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }}
        .chat-header {{
            padding: 10px;
            background: #007bff;
            color: white;
            text-align: center;
            font-size: 1.2em;
        }}
        .chat-messages {{
            padding: 20px;
            height: 300px;
            overflow-y: scroll;
            border-bottom: 1px solid #ddd;
        }}
        .chat-message {{
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }}
        .message-sender {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .message-text {{
            margin: 0;
        }}
        .chat-input {{
            display: flex;
            padding: 10px;
        }}
        .chat-input input[type="text"] {{
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
            outline: none;
        }}
        .chat-input button {{
            padding: 10px 20px;
            border: 1px solid #007bff;
            background: #007bff;
            color: white;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
        }}
        .chat-input button:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div>Room Join Code: JOIN_CODE</div>
    <br/>
    <div class="flex">
        <div class="chat-container">
            <div class="chat-header">Chat Room</div>
            <div class="chat-messages">{messages}</div>
            <div class="chat-input">
                <form method="POST" action="/">
                    <input type="text" name="message" placeholder="Type your message...">
                    <button type="submit">Send</button>
                </form>
            </div>
        </div>
    </div>
    <br/>
    <p>Reload the page to recieve updates</p>
</body>
</html>'''
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
                join_code = receive(connection)
                if join_code:
                    join_code = int.from_bytes(join_code,'big')
                    print("got join code", join_code)
                    sockets_list[connection] = []
                    initial_response = format_response(html=html_page, message_list=[]).replace('JOIN_CODE', str(join_code))
                    initial_response = len(initial_response).to_bytes(4,'big') + initial_response.encode('utf-8')
                    connection.send(initial_response)
                    color_print(f'New connection from {sockets_list[connection]} (socket {connection.fileno()})', 'green')
            else:
                try:
                    data = b""
                    data = receive(sock)
                    if data:
                        demarshalled = json.loads(data)
                        print("got data from existing connection:",demarshalled, type(demarshalled))
                        if type(demarshalled) != dict:
                            raise ValueError
                        if 'message' not in demarshalled or 'user' not in demarshalled:
                            raise KeyError
                        print('setting up resp')
                        sockets_list[sock].append((demarshalled['user'],demarshalled['message']))
                        print(sockets_list)
                        # response = json.dumps(format_response(html=html_page, message_list=sockets_list[sock][-10:]))
                        response = format_response(html=html_page, message_list=sockets_list[sock]).replace('JOIN_CODE', str(join_code))
                        response = len(response).to_bytes(4, 'big') + response.encode('utf-8')
                        print("sending resp page")
                        sock.send(response)
                        
                except ConnectionResetError:
                    print(f'Connection terminated from socket {sock.fileno()}')
                    sockets_list.pop(sock)
                except KeyError as ex:
                    print("invalid message from middleman!")
                except Exception as ex:
                    print(ex)
                    response = f"""\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Response</title>
</head>
<body>
    <h1>Server Error: {ex}</h1>
</body>
</html>
"""
                    response = len(response).to_bytes(4, 'big') + response.encode('utf-8')
                    print("sending resp: ", response)
                    sock.send(response)
                finally:
                    try:
                        sockets_list.pop(sock)
                        sock.close()
                    except Exception as ex:
                        print(ex)

                
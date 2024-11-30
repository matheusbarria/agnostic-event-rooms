import socket, select
import json
from ColorPrint import color_print
# from chat_html import html_page

MIDDLEMAN_ADDRESS = ('127.0.0.1',4999)
APPLICATION_NAME = 'connect4'
# APPLICATION_HOST = '127.0.0.2'

def local_error(message):
    color_print(message,"red")

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

def check_win(board):
    print(board)
    for icol in range(len(board)-4):
        for irow in range(len(board[0])-4):
            if (board[icol][irow]!=-1) and ((
                (board[icol][irow] == board[icol+1][irow]) and (board[icol+2][irow] == board[icol+1][irow]) and (board[icol+2][irow] == board[icol+3][irow]) and (board[icol+3][irow] == board[icol+4][irow])
            ) or (
                (board[icol][irow] == board[icol+1][irow+1]) and (board[icol+2][irow+2] == board[icol+1][irow+1]) and (board[icol+2][irow+2] == board[icol+3][irow+3]) and (board[icol+3][irow+3] == board[icol+4][irow+4])
            ) or (
                (board[icol][irow] == board[icol][irow+1]) and (board[icol][irow+2] == board[icol][irow+1]) and (board[icol][irow+2] == board[icol][irow+3]) and (board[icol][irow+3] == board[icol][irow+4])
            )):
                return True
    return False


# html_page = '<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>Chat Room</title><style>body { font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 0; display: flex; justify-content: center; align-items: center; height: 100vh; } .chat-container { width: 50%; background: white; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1); border-radius: 8px; overflow: hidden; } .chat-header { padding: 10px; background: #007bff; color: white; text-align: center; font-size: 1.2em; } .chat-messages { padding: 20px; height: 300px; overflow-y: scroll; border-bottom: 1px solid #ddd; } .chat-message { padding: 10px; border-radius: 4px; margin-bottom: 10px; } .message-sender { font-weight: bold; margin-bottom: 5px; } .message-text { margin: 0; } .chat-input { display: flex; padding: 10px; } .chat-input input[type="text"] { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px 0 0 4px; outline: none; } .chat-input button { padding: 10px 20px; border: 1px solid #007bff; background: #007bff; color: white; border-radius: 0 4px 4px 0; cursor: pointer; } .chat-input button:hover { background: #0056b3; } </style></head><body><div class="chat-container"><div class="chat-header">Chat Room</div><div class="chat-messages">{messages}</div><div class="chat-input"><input type="text" placeholder="Type your message..."><button>Send</button></div></div></body></html>'
def format_response(html,moves: dict, won=False):
    color_print(f"current moves: {moves}","yellow")
    num_players = len(moves)
    color_step = 255 if num_players==0 else int(255 / num_players)
    color_css = '\n'.join(
        f'.cell.player{i} ' + "{"
        f"  background-color: rgb({255-color_step*i},{i*color_step if i%2==0 else 0},{color_step*i})"
        "}"
        for i in range(num_players)
    )
    cells = ['<div class="cell"></div>']*42
    player_num = 0
    for player, locations in moves.items():
        for i in range(len(locations)):
            cells[locations[i]] = f'<div class="cell player{player_num}"></div>'
        player_num +=1
    cells = "\n".join(cells)
    game_won = "Game Over! Send 'reset' to restart." if won else ""

# Construct the complete room page HTML
    page = f'''\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Connect Four</title>
  <style>
    body {{
      font-family: Arial, sans-serif;
      text-align: center;
    }}
    h1 {{
      color: #333;
    }}
    #board {{
      display: grid;
      grid-template-rows: repeat(7, 50px);
      grid-template-columns: repeat(7, 50px);
      gap: 5px;
      justify-content: center;
      margin: 20px auto;
    }}
    .cell {{
      width: 50px;
      height: 50px;
      background-color: #ddd;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;
    }}
    {color_css}
    #reset {{
      margin-top: 20px;
      padding: 10px 20px;
      font-size: 16px;
      cursor: pointer;
    }}
    #status {{
      font-size: 18px;
      margin-top: 10px;
      color: #444;
    }}
  </style>
</head>
<body>
  <div>Room Join Code: JOIN_CODE</div>
  <br/>
  <h1>Connect Four</h1>
  <h1 style="color: red;">{game_won}</h1>
  <div id="board">
    <div>1</div>
    <div>2</div>
    <div>3</div>
    <div>4</div>
    <div>5</div>
    <div>6</div>
    <div>7</div>
    {cells}
  </div>
  <div id="status"></div>
  <p>Please send the column number you would like to use with your username.</p>
  <p>To reset the game send the message reset with your username.</p>
  <form method="POST" action="/">
    Username:
    <input type="text" name="client" placeholder="Type your username...">
    Message:
    <input type="text" name="message" placeholder="Type your move...">
    <button type="submit">Send</button>
</form>
</body>
</html>'''
    return page

sockets_list = {} # socket : chat_history ( not anymore)

# create a TCP socket to listen for new rooms
port = 0
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
server_socket.bind((host,port))
port = server_socket.getsockname()[1]
# TODO: make sockets list a list rather than a dict, it no longer needs to be a dict
sockets_list[server_socket] = server_socket.fileno() # master socket
room_list = dict()
board_list = dict()
server_socket.listen(2)

# Register with Middleman Server
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(registration_message(host,port)).encode(), MIDDLEMAN_ADDRESS)
sock.close()

while True:
    try:
        readable, _, _ = select.select(list(sockets_list.keys()), [], [], 0.5)
        for sock in readable:
            if sock == server_socket:
                connection, client_address = sock.accept()
                join_code = receive(connection)
                if join_code:
                    join_code = int.from_bytes(join_code,'big')
                    sockets_list[connection] = []
                    color_print(f'New connection from {sockets_list[connection]} (socket {connection.fileno()})', 'green')
                    if join_code not in room_list:
                        room_list[join_code] = {}
                        board_list[join_code] = [[-1]*6 for _ in range(7)] # column first ordering
                        initial_response = format_response(html=None, moves={}).replace('JOIN_CODE', str(join_code))
                        initial_response = len(initial_response).to_bytes(4,'big') + initial_response.encode('utf-8')
                        connection.send(initial_response)                        
            else:
                try:
                    data = b""
                    data = receive(sock)
                    if data:
                        demarshalled = json.loads(data)
                        # Verify Data
                        if type(demarshalled) != dict:
                            raise ValueError
                        if 'message' not in demarshalled or 'client' not in demarshalled or 'room' not in demarshalled:
                            raise KeyError
                        room_id = 0
                        try:
                            room_id = int(demarshalled['room'])
                        except ValueError as ex:
                            local_error('invlaid room number')
                        try:
                            col = int(demarshalled['message'])
                            if col<1 or col>7:
                                raise ValueError
                            col -= 1
                        except ValueError as ex:
                            if type(demarshalled['message'])==str and demarshalled['message']=='reset':
                                board_list[room_id] = [[-1]*6 for _ in range(7)]
                                room_list[room_id] = {}
                                response = format_response(html=None, moves=room_list[room_id]).replace('JOIN_CODE', str(join_code))
                                sock.send(response)
                                continue
                            local_error('invlaid room number')
                            raise ValueError
                        # sockets_list[sock].append((demarshalled['client'],demarshalled['message']))
                       
                        response = format_response(html=None, moves=room_list[room_id]).replace('JOIN_CODE', str(join_code))
                        # Add in the new move
                        for i in range(len(board_list[room_id][col])):
                            if board_list[room_id][col][i] == -1:
                                if check_win(board_list[room_id]):
                                    print('game won')
                                    response = format_response(html=None, moves=room_list[room_id], won=True).replace('JOIN_CODE', str(join_code))
                                else:
                                    board_list[room_id][col][i] = demarshalled['client']
                                    if demarshalled['client'] not in room_list[room_id]:
                                        room_list[room_id][demarshalled['client']] = []
                                    room_list[room_id][demarshalled['client']].append((42-7*i)-(6-col)-1)
                                    print(room_list[room_id])
                                    response = format_response(html=None, moves=room_list[room_id]).replace('JOIN_CODE', str(join_code))
                                break

                        # Send the response
                        response = len(response).to_bytes(4, 'big') + response.encode('utf-8')
                        sock.send(response)

                except ConnectionResetError:
                    local_error(f'Connection terminated from socket {sock.fileno()}')
                    sockets_list.pop(sock)
                except KeyError as ex:
                    local_error("invalid message from middleman!")
                except ValueError as ex:
                    local_error("invalid message from client!")
                    continue
                except Exception as ex:
                    local_error(ex)
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
                    sock.send(response)
                finally:
                    try:
                        sockets_list.pop(sock)
                        sock.close()
                    except Exception as ex:
                        local_error(ex)
    except socket.error as ex:
        local_error(ex)
    except Exception as ex:
        local_error(ex)

                
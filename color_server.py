import socket, select
import json
from ColorPrint import color_print
import urllib.parse

MIDDLEMAN_ADDRESS = ('127.0.0.1', 4999)
APPLICATION_NAME = 'drawing_board'

def local_error(message):
    color_print(message, "red")

def registration_message(host, port):
    return {
        "service_name": APPLICATION_NAME,
        "host": host,
        "port": port,
    }

def receive(sock):
    raw_msglen = _receive_all(sock, 4)
    if not raw_msglen:
        return None
    raw_msglen = int.from_bytes(raw_msglen, 'big')
    return _receive_all(sock, raw_msglen)

def _receive_all(sock, n):
    resp = bytearray()
    while len(resp) < n:
        data = sock.recv(n - len(resp))
        if not data:
            return None
        resp.extend(data)
    return resp

def format_response(points_list):
    points_svg = ''.join(
        f'<circle cx="{x}" cy="{y}" r="6" fill="{color}" stroke="black" stroke-width="1" />'
        for x, y, color in points_list
    )
    
    page = f'''\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Drawing Board</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}
        .drawing-container {{
            background: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 20px;
        }}
        svg {{
            border: 2px solid #ccc;
            background: white;
        }}
        .controls {{
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        input, button {{
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 8px 16px;
            cursor: pointer;
        }}
        button:hover {{
            background: #0056b3;
        }}
    </style>
</head>
<body>
    <div>Room Join Code: JOIN_CODE</div>
    <div class="drawing-container">
        <svg width="500" height="500" viewBox="0 0 500 500">
            <rect width="100%" height="100%" fill="#ffffff" />
            {points_svg}
        </svg>
        <div class="controls">
            <form method="POST" action="/">
                <input type="hidden" name="client" id="coordData">
                <input type="number" id="x" placeholder="X coordinate" min="0" max="500" required 
                       onchange="updateCoordData()" value="250">
                <input type="number" id="y" placeholder="Y coordinate" min="0" max="500" required 
                       onchange="updateCoordData()" value="250">
                <input type="color" id="color" value="#000000" onchange="updateCoordData()">
                <button type="submit">Add Point</button>
            </form>
        </div>
    </div>
    <script>
        function updateCoordData() {{
            const x = document.getElementById('x').value;
            const y = document.getElementById('y').value;
            const color = document.getElementById('color').value;
            // Using string concatenation instead of template literals to avoid f-string conflicts
            document.getElementById('coordData').value = x + ',' + y + ',' + color;
        }}
        // Initialize the coord data
        updateCoordData();
    </script>
    <p>Reload the page to see updates from other users</p>
</body>
</html>'''
    return page

sockets_list = {}
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
server_socket.bind((host, 0))
port = server_socket.getsockname()[1]
sockets_list[server_socket] = server_socket.fileno()
room_list = dict()
server_socket.listen(2)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.sendto(json.dumps(registration_message(host, port)).encode(), MIDDLEMAN_ADDRESS)
sock.close()

color_print("Drawing board server started!", "green")

while True:
    try:
        readable, _, _ = select.select(list(sockets_list.keys()), [], [], 0.5)
        for sock in readable:
            if sock == server_socket:
                connection, client_address = sock.accept()
                join_code = receive(connection)
                if join_code:
                    join_code = int.from_bytes(join_code, 'big')
                    sockets_list[connection] = []
                    color_print(f'New connection from client (socket {connection.fileno()})', 'green')
                    
                    if join_code not in room_list:
                        room_list[join_code] = []
                    initial_response = format_response(room_list[join_code]).replace('JOIN_CODE', str(join_code))
                    initial_response = len(initial_response).to_bytes(4, 'big') + initial_response.encode('utf-8')
                    connection.send(initial_response)
            else:
                try:
                    data = receive(sock)
                    if data:
                        message = json.loads(data.decode('utf-8'))
                        color_print(f"Received message: {message}", "cyan")
                        
                        room_id = message['room']
                        client_data = message.get('client')
                        
                        if client_data:
                            try:
                                decoded_data = urllib.parse.unquote(client_data)
                                color_print(f"Decoded data: {decoded_data}", "yellow")
                                x, y, color = decoded_data.split(',')
                                x = float(x)
                                y = float(y)
                                
                                color_print(f"Adding point: x={x}, y={y}, color={color}", "green")
                                room_list[room_id].append((x, y, color))
                            except json.JSONDecodeError:
                                color_print("Invalid coordinate data", "red")
                            except KeyError as e:
                                color_print(f"Missing coordinate data: {e}", "red")
                        
                        # Send updated drawing to client
                        response = format_response(room_list[room_id]).replace('JOIN_CODE', str(room_id))
                        response = len(response).to_bytes(4, 'big') + response.encode('utf-8')
                        sock.send(response)
                        
                except Exception as ex:
                    local_error(f"Error handling client message: {ex}")
                    error_response = f'''\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Error</title>
</head>
<body>
    <h1>Server Error: {str(ex)}</h1>
    <p>Please try again.</p>
</body>
</html>'''
                    error_response = len(error_response).to_bytes(4, 'big') + error_response.encode('utf-8')
                    sock.send(error_response)
                finally:
                    try:
                        sockets_list.pop(sock)
                        sock.close()
                    except Exception as ex:
                        local_error(f"Error closing socket: {ex}")
                        
    except Exception as ex:
        local_error(f"Server error: {ex}")
import socket
from threading import Thread
import json
from room import Room
import logging

def start_room(app_server_addr,room_number,base_port):
    print('in start_rooom',base_port+room_number)
    room = Room('127.0.0.1',base_port+room_number,app_server_addr,room_number)
    print(room)
    thread = Thread(target=room.start, daemon=True)
    thread.start()
    return thread

def register_application_server(application_servers, application_servers_enum):
        # UDP
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('127.0.0.1', 4999))
        while 1:
            data = sock.recv(1024)
            if data:
                data = json.loads(data)
                print(f'register application: {data}')
                if data['service_name'] not in application_servers:
                    application_servers[data['service_name']] = (data['host'],data['port'])
                    application_servers_enum.append(data['service_name'])

def handle_client(client_socket, application_servers_enum, application_servers, num_rooms, port):
    new_thread = None
    # Receive the client's request
    request = client_socket.recv(1024).decode('utf-8')
    
    if not request or not request.strip():
        client_socket.close()
        return None
        
    headers = request.split('\r\n')
    if not headers or not headers[0]:
        client_socket.close()
        return None
        
    request_parts = headers[0].split(' ')
    if len(request_parts) < 3:
        client_socket.close()
        return None
        
    method, path, _ = request_parts

    # If the request is a GET request to "/"
    if method == "GET" and path == "/":
        response = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form for 5000</title>
</head>
<body style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background-color: #f4f4f4;">
    <h1>Event Rooms!</h1>
    <br/>
    <h3>Select an Application to Create a Room:</h3>
    <ol style="list-style-position: inside;"> {application_servers} </ol>
    <br/>
    <form method="POST" action="/">
        <label for="appNum">Select an Application:</label>
        <input type="text" id="appNum" name="appNum" required>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""
        application_servers_list = ''.join(f'<li>{server}</li>' for server in application_servers_enum)
        html_content = response.format(application_servers=application_servers_list)
        client_socket.send(html_content.encode('utf-8'))

    # If the request is a POST request to "/"
    elif method == "POST" and path == "/":
        try:
            app_num = int(headers[-1].split('=')[-1]) - 1
            app_addr = application_servers[application_servers_enum[app_num]]
            new_thread = start_room(app_addr,num_rooms+1,port)
            response = """\
HTTP/1.1 302 Found
Location: http://127.0.0.1:""" + str(port+num_rooms+1) + "\n"
            print(f"sending\n{response}")
            client_socket.send(response.encode('utf-8'))
        except Exception as ex:
            print(f"error in post {ex}")
            response = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form for 5000</title>
</head>
<body style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background-color: #f4f4f4;">
    <h1>Event Rooms!</h1>
    <br/>
    <h3>Select an Application to Create a Room:</h3>
    <h3>Please enter a valid application room number</h3>
    <ol style="list-style-position: inside;"> {application_servers} </ol>
    <br/>
    <form method="POST" action="/">
        <label for="appNum">Select an Application:</label>
        <input type="text" id="appNum" name="appNum" required>
        <input type="submit" value="Submit">
    </form>
</body>
</html>
"""
            application_servers_list = ''.join(f'<li>{server}</li>' for server in application_servers_enum)
            html_content = response.format(application_servers=application_servers_list)
            client_socket.send(html_content.encode('utf-8'))
    client_socket.close()

    return new_thread

def start_server(port):
    thread_count = 0
    application_servers_enum = []
    application_servers = {}  # Format: {'service_name': ('ip', port)}
    rooms = {}  # Format: {'join_code': Room}

    name_thread = Thread(target=register_application_server, args=(application_servers, application_servers_enum))
    name_thread.daemon = True
    name_thread.start()

    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('127.0.0.1', port))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        print("Server listening on 127.0.0.1:"+str(port))
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")
                ret = handle_client(client_socket, application_servers_enum, application_servers, thread_count,port=port)
                if ret:
                    rooms[thread_count] = ret
                    thread_count+=1
            except socket.timeout:
                continue # timeout allows for accepting signals (ctrl c)
            except socket.error as ex:
                print(f'match maker socket error: {ex}')
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server_socket.close()
        print("Socket closed.")

if __name__ == "__main__":
    start_server(5050)

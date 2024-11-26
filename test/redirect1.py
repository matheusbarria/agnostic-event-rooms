import socket

def handle_client(client_socket):
    # Receive the client's request
    request = client_socket.recv(1024).decode('utf-8')
    headers = request.split('\r\n')
    method, path, _ = headers[0].split(' ')

    # If the request is a GET request to "/"
    if method == "GET" and path == "/":
        response = """\
HTTP/1.1 200 OK

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Form for 5001</title>
</head>
<body>
    <h1>Submit Your Data to 5001</h1>
    <form method="POST" action="/">
        <label for="inputField">Enter something:</label>
        <input type="text" id="inputField" name="inputField">
        <button type="submit">Submit</button>
    </form>
</body>
</html>
"""
        client_socket.send(response.encode('utf-8'))

    # If the request is a POST request to "/"
    elif method == "POST" and path == "/":
        response = """\
HTTP/1.1 302 Found
Location: http://127.0.0.1:5000

"""
        client_socket.send(response.encode('utf-8'))

    # Close the client socket
    client_socket.close()

def start_server():
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.bind(('127.0.0.1', 5001))
        server_socket.listen(5)
        server_socket.settimeout(1.0)
        print("Server listening on 127.0.0.1:5001...")
        
        while True:
            try:
                client_socket, client_address = server_socket.accept()
                print(f"Connection from {client_address}")
                handle_client(client_socket)
            except socket.timeout:
                continue # timeout allows for accepting signals (ctrl c)
    except KeyboardInterrupt:
        print("\nServer stopped.")
    finally:
        server_socket.close()
        print("Socket closed.")

# Start the server
if __name__ == "__main__":
    start_server()

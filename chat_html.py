html_page = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat Room</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f4;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .chat-container {
            width: 50%;
            background: white;
            box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        .chat-header {
            padding: 10px;
            background: #007bff;
            color: white;
            text-align: center;
            font-size: 1.2em;
        }
        .chat-messages {
            padding: 20px;
            height: 300px;
            overflow-y: scroll;
            border-bottom: 1px solid #ddd;
        }
        .chat-message {
            padding: 10px;
            border-radius: 4px;
            margin-bottom: 10px;
        }
        .message-sender {
            font-weight: bold;
            margin-bottom: 5px;
        }
        .message-text {
            margin: 0;
        }
        .chat-input {
            display: flex;
            padding: 10px;
        }
        .chat-input input[type="text"] {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px 0 0 4px;
            outline: none;
        }
        .chat-input button {
            padding: 10px 20px;
            border: 1px solid #007bff;
            background: #007bff;
            color: white;
            border-radius: 0 4px 4px 0;
            cursor: pointer;
        }
        .chat-input button:hover {
            background: #0056b3;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            Chat Room
        </div>
        <div class="chat-messages">
            {messages}
        </div>
        <div class="chat-input">
            <input type="text" placeholder="Type your message...">
            <button>Send</button>
        </div>
    </div>
</body>
</html>
'''
import socket, select
import json
import struct

MIDDLEMAN_ADDRESS = ('127.0.0.1',5001)
APPLICATION_NAME = 'trivia'

from trivia_html import TRIVIA_HTML

class TriviaGame:
    def __init__(self):
        self.questions = [
            {
                "question": "What is the capital of France?",
                "options": ["London", "Berlin", "Paris", "Madrid"],
                "correct": 2
            },
            {
                "question": "Which planet is known as the Red Planet?",
                "options": ["Venus", "Mars", "Jupiter", "Saturn"],
                "correct": 1
            }
        ]
        self.current_question = 0
        self.scores = {}
        
    def get_current_question(self):
        if self.current_question < len(self.questions):
            return self.questions[self.current_question]
        return {"question": "Game Over!", "options": [], "correct": -1}
    
    def check_answer(self, answer):
        if self.current_question < len(self.questions):
            return answer == self.questions[self.current_question]["correct"]
        return False
    
    def next_question(self):
        self.current_question += 1
        return self.current_question < len(self.questions)

    def format_html(self):
        current_q = self.get_current_question()
        options_html = ''.join([
            f'<button class="option-button" onclick="sendAnswer({i})">{opt}</button>'
            for i, opt in enumerate(current_q["options"])
        ])
        
        scores_html = ''.join([
            f'<div class="player-score">Player {player}: {score}</div>'
            for player, score in self.scores.items()
        ]) if self.scores else '<div class="player-score">No scores yet</div>'
        
        return TRIVIA_HTML.format(
            question=current_q["question"],
            options=options_html,
            scores=scores_html
        )

def receive_message(sock):
    try:
        length_bytes = sock.recv(4)
        if not length_bytes:
            return None
        length = struct.unpack('!I', length_bytes)[0]
        data = sock.recv(length)
        return data
    except Exception as e:
        print(f"Error receiving message: {e}")
        return None

def send_message(sock, data):
    try:
        length = len(data)
        sock.sendall(struct.pack('!I', length))
        sock.sendall(data)
    except Exception as e:
        print(f"Error sending message: {e}")

games = {}  # socket: TriviaGame

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
server_socket.bind((host, 0))
port = server_socket.getsockname()[1]
server_socket.listen(5)

registration_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
registration_message = {
    "service_name": APPLICATION_NAME,
    "host": host,
    "port": port,
}
registration_sock.sendto(json.dumps(registration_message).encode(), MIDDLEMAN_ADDRESS)
registration_sock.close()

print(f"Trivia server started on {host}:{port}")

while True:
    sockets_list = [server_socket] + list(games.keys())
    readable, _, exceptional = select.select(sockets_list, [], sockets_list)

    for sock in readable:
        if sock == server_socket:
            client_socket, address = sock.accept()
            print(f"New connection from {address}")
            
            game = TriviaGame()
            games[client_socket] = game
            
            response = game.format_html()
            send_message(client_socket, response.encode())
            
        else:
            data = receive_message(sock)
            if data:
                try:
                    game = games[sock]
                    message = json.loads(data.decode())
                    
                    if "answer" in message:
                        correct = game.check_answer(message["answer"])
                        if correct:
                            game.scores[sock.fileno()] = game.scores.get(sock.fileno(), 0) + 1
                        game.next_question()
                        
                        state = {
                            "question": game.get_current_question(),
                            "scores": game.scores
                        }
                        send_message(sock, json.dumps(state).encode())
                except json.JSONDecodeError:
                    game = games[sock]
                    response = game.format_html()
                    send_message(sock, response.encode())
            else:
                print(f"Client {sock.getpeername()} disconnected")
                games.pop(sock, None)
                sock.close()

    for sock in exceptional:
        print(f"Exceptional condition for {sock.getpeername()}")
        games.pop(sock, None)
        sock.close()




# from fastapi import FastAPI, WebSocket, WebSocketDisconnect
# import logging
# from typing import Dict, Set, List
# import json
# import random
# import asyncio
# import httpx  # We'll use this to make HTTP requests

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# app = FastAPI()

# async def fetch_trivia_questions():
#     """Fetch questions from the OpenTrivia API"""
#     async with httpx.AsyncClient() as client:
#         response = await client.get(
#             "https://opentdb.com/api.php",
#             params={
#                 "amount": 15,
#                 "category": 9,  # General Knowledge
#                 "type": "multiple"
#             }
#         )
#         data = response.json()
        
#         if data["response_code"] == 0:  # Success
#             questions = []
#             for q in data['results']:
#                 # Combine correct and incorrect answers
#                 options = [q['correct_answer']] + q['incorrect_answers']
#                 random.shuffle(options)
#                 correct_index = options.index(q['correct_answer'])
                
#                 questions.append({
#                     'question': q['question'],
#                     'options': options,
#                     'correct': correct_index,
#                     'category': q['category'],
#                     'difficulty': q['difficulty']
#                 })
#             return questions
#         return []

# class TriviaGame:
#     def __init__(self):
#         self.current_question: int = 0
#         self.scores: Dict[str, int] = {}
#         self.questions: List[dict] = []
#         self.state: str = "waiting"  # waiting, question, reveal
#         self.answered_players: Set[str] = set()

#     async def initialize_questions(self):
#         """Fetch and initialize questions when game starts"""
#         self.questions = await fetch_trivia_questions()
#         self.current_question = 0
#         return bool(self.questions)  # Return True if we got questions

#     def add_player(self, username: str):
#         if username not in self.scores:
#             self.scores[username] = 0

#     def submit_answer(self, username: str, answer: int) -> bool:
#         if (self.state == "question" and 
#             username in self.scores and 
#             username not in self.answered_players):
#             correct = self.questions[self.current_question]["correct"] == answer
#             if correct:
#                 self.scores[username] += 1
#             self.answered_players.add(username)
#             return correct
#         return False

#     def next_question(self) -> dict:
#         if self.current_question < len(self.questions):
#             question = self.questions[self.current_question].copy()
#             # Include category and difficulty but remove correct answer
#             response = {
#                 'question': question['question'],
#                 'options': question['options'],
#                 'category': question['category'],
#                 'difficulty': question['difficulty']
#             }
#             self.answered_players.clear()  # Reset answered players for new question
#             return response
#         return None

# class ConnectionManager:
#     def __init__(self):
#         self.active_rooms: Dict[str, Set[WebSocket]] = {}
#         self.games: Dict[str, TriviaGame] = {}

#     async def connect(self, websocket: WebSocket, room_id: str):
#         await websocket.accept()
#         if room_id not in self.active_rooms:
#             self.active_rooms[room_id] = set()
#             self.games[room_id] = TriviaGame()
#         self.active_rooms[room_id].add(websocket)
#         logger.info(f"Client connected to room {room_id}. Total clients: {len(self.active_rooms[room_id])}")

#     def disconnect(self, websocket: WebSocket, room_id: str):
#         self.active_rooms[room_id].remove(websocket)
#         if len(self.active_rooms[room_id]) == 0:
#             del self.active_rooms[room_id]
#             del self.games[room_id]
#             logger.info(f"Room {room_id} was deleted")
#         logger.info(f"Client disconnected from room {room_id}")

#     async def broadcast(self, message: str, room_id: str, sender: WebSocket = None):
#         if room_id in self.active_rooms:
#             for connection in self.active_rooms[room_id]:
#                 if connection != sender:
#                     await connection.send_text(message)

# manager = ConnectionManager()

# @app.get("/")
# def read_root():
#     return {"Hello": "World"}

# @app.websocket("/ws/{room_id}")
# async def websocket_endpoint(websocket: WebSocket, room_id: str):
#     await manager.connect(websocket, room_id)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             message_data = json.loads(data)
#             game = manager.games[room_id]
            
#             if message_data["type"] == "join":
#                 # Player joining the game
#                 username = message_data["username"]
#                 game.add_player(username)
#                 response = json.dumps({
#                     "type": "player_joined",
#                     "username": username,
#                     "scores": game.scores
#                 })
#                 await websocket.send_text(response)
#                 await manager.broadcast(response, room_id, websocket)

#             elif message_data["type"] == "start_game":
#                 # Initialize questions and start the game
#                 success = await game.initialize_questions()
#                 if success:
#                     game.state = "question"
#                     question = game.next_question()
#                     response = json.dumps({
#                         "type": "question",
#                         "question": question
#                     })
#                     await manager.broadcast(response, room_id)
#                     await websocket.send_text(response)
#                 else:
#                     error_response = json.dumps({
#                         "type": "error",
#                         "message": "Failed to fetch questions. Please try again."
#                     })
#                     await websocket.send_text(error_response)

#             elif message_data["type"] == "answer":
#                 # Player submitting an answer
#                 correct = game.submit_answer(
#                     message_data["username"],
#                     message_data["answer"]
#                 )
#                 response = json.dumps({
#                     "type": "answer_received",
#                     "username": message_data["username"]
#                 })
#                 await manager.broadcast(response, room_id)
                
#                 # Check if all players have answered
#                 if len(game.answered_players) == len(game.scores):
#                     game.state = "reveal"
#                     response = json.dumps({
#                         "type": "reveal",
#                         "correct_answer": game.questions[game.current_question]["correct"],
#                         "scores": game.scores
#                     })
#                     await manager.broadcast(response, room_id)
#                     await websocket.send_text(response)
                    
#                     # Move to next question after delay
#                     await asyncio.sleep(3)
#                     game.current_question += 1
#                     game.state = "question"
                    
#                     question = game.next_question()
#                     if question:
#                         response = json.dumps({
#                             "type": "question",
#                             "question": question
#                         })
#                         await manager.broadcast(response, room_id)
#                         await websocket.send_text(response)
#                     else:
#                         # Game over
#                         response = json.dumps({
#                             "type": "game_over",
#                             "final_scores": game.scores
#                         })
#                         await manager.broadcast(response, room_id)
#                         await websocket.send_text(response)

#     except WebSocketDisconnect:
#         manager.disconnect(websocket, room_id)
#     except Exception as e:
#         logger.error(f"Error in room {room_id}: {str(e)}")
#         manager.disconnect(websocket, room_id)
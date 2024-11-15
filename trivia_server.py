from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
from typing import Dict, Set, List
import json
import random
import asyncio
import httpx  # We'll use this to make HTTP requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

async def fetch_trivia_questions():
    """Fetch questions from the OpenTrivia API"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://opentdb.com/api.php",
            params={
                "amount": 15,
                "category": 9,  # General Knowledge
                "type": "multiple"
            }
        )
        data = response.json()
        
        if data["response_code"] == 0:  # Success
            questions = []
            for q in data['results']:
                # Combine correct and incorrect answers
                options = [q['correct_answer']] + q['incorrect_answers']
                random.shuffle(options)
                correct_index = options.index(q['correct_answer'])
                
                questions.append({
                    'question': q['question'],
                    'options': options,
                    'correct': correct_index,
                    'category': q['category'],
                    'difficulty': q['difficulty']
                })
            return questions
        return []

class TriviaGame:
    def __init__(self):
        self.current_question: int = 0
        self.scores: Dict[str, int] = {}
        self.questions: List[dict] = []
        self.state: str = "waiting"  # waiting, question, reveal
        self.answered_players: Set[str] = set()

    async def initialize_questions(self):
        """Fetch and initialize questions when game starts"""
        self.questions = await fetch_trivia_questions()
        self.current_question = 0
        return bool(self.questions)  # Return True if we got questions

    def add_player(self, username: str):
        if username not in self.scores:
            self.scores[username] = 0

    def submit_answer(self, username: str, answer: int) -> bool:
        if (self.state == "question" and 
            username in self.scores and 
            username not in self.answered_players):
            correct = self.questions[self.current_question]["correct"] == answer
            if correct:
                self.scores[username] += 1
            self.answered_players.add(username)
            return correct
        return False

    def next_question(self) -> dict:
        if self.current_question < len(self.questions):
            question = self.questions[self.current_question].copy()
            # Include category and difficulty but remove correct answer
            response = {
                'question': question['question'],
                'options': question['options'],
                'category': question['category'],
                'difficulty': question['difficulty']
            }
            self.answered_players.clear()  # Reset answered players for new question
            return response
        return None

class ConnectionManager:
    def __init__(self):
        self.active_rooms: Dict[str, Set[WebSocket]] = {}
        self.games: Dict[str, TriviaGame] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = set()
            self.games[room_id] = TriviaGame()
        self.active_rooms[room_id].add(websocket)
        logger.info(f"Client connected to room {room_id}. Total clients: {len(self.active_rooms[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_rooms[room_id].remove(websocket)
        if len(self.active_rooms[room_id]) == 0:
            del self.active_rooms[room_id]
            del self.games[room_id]
            logger.info(f"Room {room_id} was deleted")
        logger.info(f"Client disconnected from room {room_id}")

    async def broadcast(self, message: str, room_id: str, sender: WebSocket = None):
        if room_id in self.active_rooms:
            for connection in self.active_rooms[room_id]:
                if connection != sender:
                    await connection.send_text(message)

manager = ConnectionManager()

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.websocket("/ws/{room_id}")
async def websocket_endpoint(websocket: WebSocket, room_id: str):
    await manager.connect(websocket, room_id)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            game = manager.games[room_id]
            
            if message_data["type"] == "join":
                # Player joining the game
                username = message_data["username"]
                game.add_player(username)
                response = json.dumps({
                    "type": "player_joined",
                    "username": username,
                    "scores": game.scores
                })
                await websocket.send_text(response)
                await manager.broadcast(response, room_id, websocket)

            elif message_data["type"] == "start_game":
                # Initialize questions and start the game
                success = await game.initialize_questions()
                if success:
                    game.state = "question"
                    question = game.next_question()
                    response = json.dumps({
                        "type": "question",
                        "question": question
                    })
                    await manager.broadcast(response, room_id)
                    await websocket.send_text(response)
                else:
                    error_response = json.dumps({
                        "type": "error",
                        "message": "Failed to fetch questions. Please try again."
                    })
                    await websocket.send_text(error_response)

            elif message_data["type"] == "answer":
                # Player submitting an answer
                correct = game.submit_answer(
                    message_data["username"],
                    message_data["answer"]
                )
                response = json.dumps({
                    "type": "answer_received",
                    "username": message_data["username"]
                })
                await manager.broadcast(response, room_id)
                
                # Check if all players have answered
                if len(game.answered_players) == len(game.scores):
                    game.state = "reveal"
                    response = json.dumps({
                        "type": "reveal",
                        "correct_answer": game.questions[game.current_question]["correct"],
                        "scores": game.scores
                    })
                    await manager.broadcast(response, room_id)
                    await websocket.send_text(response)
                    
                    # Move to next question after delay
                    await asyncio.sleep(3)
                    game.current_question += 1
                    game.state = "question"
                    
                    question = game.next_question()
                    if question:
                        response = json.dumps({
                            "type": "question",
                            "question": question
                        })
                        await manager.broadcast(response, room_id)
                        await websocket.send_text(response)
                    else:
                        # Game over
                        response = json.dumps({
                            "type": "game_over",
                            "final_scores": game.scores
                        })
                        await manager.broadcast(response, room_id)
                        await websocket.send_text(response)

    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        logger.error(f"Error in room {room_id}: {str(e)}")
        manager.disconnect(websocket, room_id)
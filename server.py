from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import logging
from typing import Dict, Set
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

class ConnectionManager:
    def __init__(self):
        self.active_rooms: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str):
        await websocket.accept()
        if room_id not in self.active_rooms:
            self.active_rooms[room_id] = set()
        self.active_rooms[room_id].add(websocket)
        logger.info(f"Client connected to room {room_id}. Total clients in room: {len(self.active_rooms[room_id])}")

    def disconnect(self, websocket: WebSocket, room_id: str):
        self.active_rooms[room_id].remove(websocket)
        if len(self.active_rooms[room_id]) == 0:
            del self.active_rooms[room_id]
            logger.info(f"Room {room_id} was deleted")
        logger.info(f"Client disconnected from room {room_id}. Total clients in room: {len(self.active_rooms[room_id])}")

    async def broadcast(self, message: str, room_id: str, sender: WebSocket):
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
            username = message_data.get("username", "Anonymous")
            message = message_data.get("message", "")
            response = json.dumps({
                "username": username,
                "message": message,
                "room_id": room_id
            })
            
            await websocket.send_text(response)
            await manager.broadcast(response, room_id, websocket)
            
            logger.info(f"Message in room {room_id} from {username}: {message}")
            
    except WebSocketDisconnect:
        manager.disconnect(websocket, room_id)
    except Exception as e:
        logger.error(f"Error in room {room_id}: {str(e)}")
        manager.disconnect(websocket, room_id)
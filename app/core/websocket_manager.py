import asyncio
from typing import Dict, Set

from fastapi import WebSocket

from app.core.schema import WSMessage


class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, Set[WebSocket]] = {}
        self.lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket, room: str):
        await websocket.accept()
        async with self.lock:
            self.rooms.setdefault(room, set()).add(websocket)

    async def disconnect(self, websocket: WebSocket, room: str):
        async with self.lock:
            if room in self.rooms:
                self.rooms[room].discard(websocket)
                if not self.rooms[room]:
                    del self.rooms[room]

    async def broadcast(self, room: str, message: WSMessage):
        async with self.lock:
            sockets = list(self.rooms.get(room, []))

        for ws in sockets:
            await ws.send_json(message)

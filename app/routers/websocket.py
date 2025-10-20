from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import List
import json

router = APIRouter()

# Lista de conexiones activas
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Enviar mensaje a todas las conexiones activas"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                # Si falla, remover la conexión
                self.active_connections.remove(connection)

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Recibir mensajes del cliente (si es necesario)
            data = await websocket.receive_text()
            # Aquí puedes procesar mensajes del cliente si lo necesitas
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Función auxiliar para enviar notificaciones
async def notify_clients(message_type: str, data: dict):
    """
    Envía una notificación a todos los clientes conectados
    message_type: "espacio_update", "nueva_asignacion", "nuevo_incidente", etc.
    """
    message = {
        "type": message_type,
        "data": data
    }
    await manager.broadcast(message)
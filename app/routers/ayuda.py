# Crear archivo: backend/app/routers/ayuda.py

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from ..database import get_db
from ..models import SolicitudAyuda
from ..schemas import SolicitudAyudaCreate, SolicitudAyudaResponse, SolicitudAyudaUpdate

router = APIRouter(prefix="/ayuda", tags=["Ayuda"])

# Almacenar conexiones WebSocket activas para notificaciones en tiempo real
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"✅ Nueva conexión WebSocket. Total: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        print(f"❌ Conexión WebSocket cerrada. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """Enviar mensaje a todos los clientes conectados"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error enviando mensaje: {e}")

manager = ConnectionManager()

# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/solicitar", response_model=SolicitudAyudaResponse)
async def solicitar_ayuda(
    solicitud: SolicitudAyudaCreate,
    db: Session = Depends(get_db)
):
    """
    Crear una nueva solicitud de ayuda.
    Usado por la interfaz de usuario (pantalla táctil).
    """
    try:
        # Crear nueva solicitud
        nueva_solicitud = SolicitudAyuda(
            fecha_hora=datetime.now(),
            ubicacion=solicitud.ubicacion,
            atendida=False
        )
        
        db.add(nueva_solicitud)
        db.commit()
        db.refresh(nueva_solicitud)
        
        # Notificar a todos los administradores conectados via WebSocket
        await manager.broadcast({
            "type": "nueva_solicitud_ayuda",
            "data": {
                "id": nueva_solicitud.id,
                "fecha_hora": nueva_solicitud.fecha_hora.isoformat(),
                "ubicacion": nueva_solicitud.ubicacion,
                "mensaje": "Nueva solicitud de ayuda recibida"
            }
        })
        
        print(f"🆘 Nueva solicitud de ayuda: ID {nueva_solicitud.id}")
        
        return nueva_solicitud
        
    except Exception as e:
        db.rollback()
        print(f"Error al crear solicitud de ayuda: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear solicitud: {str(e)}")

@router.get("/pendientes", response_model=List[SolicitudAyudaResponse])
def obtener_solicitudes_pendientes(db: Session = Depends(get_db)):
    """
    Obtener todas las solicitudes de ayuda pendientes (no atendidas).
    Usado por el panel de administración.
    """
    solicitudes = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.atendida == False
    ).order_by(
        SolicitudAyuda.fecha_hora.desc()
    ).all()
    
    return solicitudes

@router.get("/todas", response_model=List[SolicitudAyudaResponse])
def obtener_todas_solicitudes(
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """
    Obtener todas las solicitudes de ayuda (atendidas y pendientes).
    Con límite de resultados.
    """
    solicitudes = db.query(SolicitudAyuda).order_by(
        SolicitudAyuda.fecha_hora.desc()
    ).limit(limit).all()
    
    return solicitudes

@router.get("/{solicitud_id}", response_model=SolicitudAyudaResponse)
def obtener_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    """
    Obtener una solicitud específica por ID.
    """
    solicitud = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.id == solicitud_id
    ).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    return solicitud

@router.put("/{solicitud_id}/atender", response_model=SolicitudAyudaResponse)
async def marcar_como_atendida(
    solicitud_id: int,
    update: SolicitudAyudaUpdate,
    db: Session = Depends(get_db)
):
    """
    Marcar una solicitud como atendida.
    Opcionalmente agregar notas.
    """
    solicitud = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.id == solicitud_id
    ).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Actualizar campos
    if update.atendida is not None:
        solicitud.atendida = update.atendida
        if update.atendida:
            solicitud.fecha_hora_atencion = datetime.now()
    
    if update.notas is not None:
        solicitud.notas = update.notas
    
    db.commit()
    db.refresh(solicitud)
    
    # Notificar actualización via WebSocket
    await manager.broadcast({
        "type": "solicitud_atendida",
        "data": {
            "id": solicitud.id,
            "atendida": solicitud.atendida
        }
    })
    
    return solicitud

@router.delete("/{solicitud_id}")
async def eliminar_solicitud(solicitud_id: int, db: Session = Depends(get_db)):
    """
    Eliminar una solicitud de ayuda.
    """
    solicitud = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.id == solicitud_id
    ).first()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    db.delete(solicitud)
    db.commit()
    
    return {"message": "Solicitud eliminada exitosamente"}

# ============================================================
# WEBSOCKET
# ============================================================

@router.websocket("/ws")
async def websocket_ayuda(websocket: WebSocket):
    """
    WebSocket para notificaciones en tiempo real de solicitudes de ayuda.
    Los administradores se conectan aquí para recibir alertas.
    """
    await manager.connect(websocket)
    try:
        while True:
            # Mantener conexión abierta
            data = await websocket.receive_text()
            
            # El cliente puede enviar "ping" para mantener viva la conexión
            if data == "ping":
                await websocket.send_text("pong")
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# ============================================================
# ESTADÍSTICAS
# ============================================================

@router.get("/stats/resumen")
def obtener_resumen_ayuda(db: Session = Depends(get_db)):
    """
    Obtener estadísticas resumidas de solicitudes de ayuda.
    """
    total = db.query(SolicitudAyuda).count()
    pendientes = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.atendida == False
    ).count()
    atendidas = db.query(SolicitudAyuda).filter(
        SolicitudAyuda.atendida == True
    ).count()
    
    return {
        "total": total,
        "pendientes": pendientes,
        "atendidas": atendidas,
        "porcentaje_atencion": round((atendidas / total * 100), 2) if total > 0 else 0
    }
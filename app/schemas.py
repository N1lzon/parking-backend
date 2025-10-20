from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ============ USUARIO SCHEMAS ============
class UsuarioBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    contraseña: str = Field(..., min_length=4)

class UsuarioCreate(UsuarioBase):
    pass

class UsuarioResponse(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True

class UsuarioLogin(BaseModel):
    nombre: str
    contraseña: str


# ============ ESPACIO SCHEMAS ============
class EspacioBase(BaseModel):
    numero_de_espacio: str
    estado: str = "libre"  # libre, ocupado, reservado

class EspacioCreate(EspacioBase):
    pass

class EspacioUpdate(BaseModel):
    estado: Optional[str] = None

class EspacioResponse(BaseModel):
    id: int
    numero_de_espacio: str
    estado: str
    
    class Config:
        from_attributes = True


# ============ ASIGNACION SCHEMAS ============
class AsignacionBase(BaseModel):
    id_de_espacio: int
    id_usuario: Optional[int] = None

class AsignacionCreate(BaseModel):
    id_usuario: Optional[int] = None  # Para usuarios especiales

class AsignacionResponse(BaseModel):
    id: int
    id_de_espacio: int
    id_usuario: Optional[int]
    asignado_a: datetime
    liberado_a: Optional[datetime]
    espacio: EspacioResponse
    
    class Config:
        from_attributes = True


# ============ INCIDENTE SCHEMAS ============
class IncidenteBase(BaseModel):
    id_de_espacio: int
    tipo_de_incidente: str
    nota: Optional[str] = None

class IncidenteCreate(IncidenteBase):
    pass

class IncidenteUpdate(BaseModel):
    hora_de_solucion: Optional[datetime] = None
    nota: Optional[str] = None

class IncidenteResponse(BaseModel):
    id: int
    id_de_espacio: int
    tipo_de_incidente: str
    hora_de_registro: datetime
    hora_de_solucion: Optional[datetime]
    nota: Optional[str]
    espacio: EspacioResponse
    
    class Config:
        from_attributes = True


# ============ REPORTES SCHEMAS ============
class ReporteRequest(BaseModel):
    fecha_inicio: datetime
    fecha_fin: datetime

class EstadisticasResponse(BaseModel):
    total_espacios: int
    espacios_disponibles: int
    espacios_ocupados: int
    espacios_reservados: int
    total_asignaciones: int
    total_incidentes: int
    promedio_horas_ocupacion: float


# ============ WEBSOCKET MESSAGES ============
class WebSocketMessage(BaseModel):
    type: str  # "espacio_update", "nueva_asignacion", "nuevo_incidente"
    data: dict
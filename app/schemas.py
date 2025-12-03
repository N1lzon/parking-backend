from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

# ============ ADMIN SCHEMAS ============
class AdminBase(BaseModel):
    nombre: str = Field(..., min_length=1, max_length=100)
    contraseña: str = Field(..., min_length=4)

class AdminCreate(AdminBase):
    pass

class AdminResponse(BaseModel):
    id: int
    nombre: str
    
    class Config:
        from_attributes = True

class AdminLogin(BaseModel):
    nombre: str
    contraseña: str


# ============ USUARIO RESERVA SCHEMAS ============
class UsuarioReservaBase(BaseModel):
    ci: int = Field(..., gt=0)
    nombre: str = Field(..., min_length=1, max_length=100)

class UsuarioReservaCreate(UsuarioReservaBase):
    pass

class UsuarioReservaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, max_length=100)

class UsuarioReservaResponse(BaseModel):
    ci: int
    nombre: str
    
    class Config:
        from_attributes = True


# ============ ESPACIO SCHEMAS ============
class EspacioBase(BaseModel):
    numero_de_espacio: int = Field(..., gt=0)
    estado: str = "libre"  # libre, ocupado
    reservado: str = "no"  # si, no

class EspacioCreate(EspacioBase):
    pass

class EspacioUpdate(BaseModel):
    estado: Optional[str] = None
    reservado: Optional[str] = None

class EspacioResponse(BaseModel):
    id: int
    numero_de_espacio: int
    estado: str
    reservado: str
    
    class Config:
        from_attributes = True


# ============ ASIGNACION SCHEMAS ============
class AsignacionBase(BaseModel):
    ci_reserva: Optional[int] = None
    id_de_espacio: int

class AsignacionCreate(BaseModel):
    ci: Optional[int] = None  # CI del usuario con reserva, o null para usuario normal

class AsignacionResponse(BaseModel):
    id: int
    ci_reserva: Optional[int]
    id_de_espacio: int
    hora_asignado: datetime
    hora_liberado: Optional[datetime]
    espacio: EspacioResponse
    usuario_reserva: Optional[UsuarioReservaResponse] = None
    
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


class AdminBase(BaseModel):
    nombre: str

class AdminCreate(AdminBase):
    contraseña: str

class AdminUpdate(BaseModel):
    nombre: Optional[str] = None
    contraseña: Optional[str] = None

class AdminResponse(AdminBase):
    id: int
    fecha_creacion: Optional[datetime]
    ultimo_login: Optional[datetime]

    class Config:
        orm_mode = True

class AdminLogin(BaseModel):
    nombre: str
    contraseña: str
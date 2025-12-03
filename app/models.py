from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import pytz
from datetime import datetime

paraguay_tz = pytz.timezone("America/Asuncion")

class Admin(Base):
    __tablename__ = "admin"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False, unique=True)
    contraseña = Column(String(255), nullable=False)  # En producción usar hash
    fecha_creacion = Column(DateTime(timezone=True), default=lambda: datetime.now(paraguay_tz))
    ultimo_login = Column(DateTime(timezone=True), nullable=True)


class UsuarioReserva(Base):
    __tablename__ = "usuario_reserva"

    ci = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    
    # Relación con asignaciones
    asignaciones = relationship("Asignacion", back_populates="usuario_reserva")


class Espacio(Base):
    __tablename__ = "espacio"

    id = Column(Integer, primary_key=True, index=True)
    numero_de_espacio = Column(Integer, unique=True, nullable=False)  # 1, 2, 3, ..., 20
    estado = Column(String(20), nullable=False, default="libre")  # libre, ocupado
    reservado = Column(String(5), nullable=False, default="no")  # si, no
    
    # Relaciones
    asignaciones = relationship("Asignacion", back_populates="espacio")
    incidentes = relationship("Incidente", back_populates="espacio")


class Asignacion(Base):
    __tablename__ = "asignacion"

    id = Column(Integer, primary_key=True, index=True)
    ci_reserva = Column(Integer, ForeignKey("usuario_reserva.ci"), nullable=True)  # Null para usuarios normales
    id_de_espacio = Column(Integer, ForeignKey("espacio.id"), nullable=False)
    hora_asignado = Column(DateTime(timezone=True), server_default=func.now())
    hora_liberado = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    espacio = relationship("Espacio", back_populates="asignaciones")
    usuario_reserva = relationship("UsuarioReserva", back_populates="asignaciones")


class Incidente(Base):
    __tablename__ = "incidente"

    id = Column(Integer, primary_key=True, index=True)
    id_de_espacio = Column(Integer, ForeignKey("espacio.id"), nullable=False)
    tipo_de_incidente = Column(String(100), nullable=False)  # ocupación sin asignar, sensor fuera de funcionamiento, etc.
    hora_de_registro = Column(DateTime(timezone=True), server_default=func.now())
    hora_de_solucion = Column(DateTime(timezone=True), nullable=True)
    nota = Column(Text, nullable=True)
    
    # Relación
    espacio = relationship("Espacio", back_populates="incidentes")
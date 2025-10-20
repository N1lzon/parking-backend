from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(100), nullable=False)
    contraseña = Column(String(255), nullable=False)  # En producción usar hash
    
    # Relación con asignaciones
    asignaciones = relationship("Asignacion", back_populates="usuario")


class Espacio(Base):
    __tablename__ = "espacios"

    id = Column(Integer, primary_key=True, index=True)
    numero_de_espacio = Column(String(10), unique=True, nullable=False)  # "01", "02", etc.
    estado = Column(String(20), nullable=False, default="libre")  # libre, ocupado, reservado
    
    # Relaciones
    asignaciones = relationship("Asignacion", back_populates="espacio")
    incidentes = relationship("Incidente", back_populates="espacio")


class Asignacion(Base):
    __tablename__ = "asignaciones"

    id = Column(Integer, primary_key=True, index=True)
    id_de_espacio = Column(Integer, ForeignKey("espacios.id"), nullable=False)
    id_usuario = Column(Integer, ForeignKey("usuarios.id"), nullable=True)  # Null para usuarios anónimos
    asignado_a = Column(DateTime(timezone=True), server_default=func.now())
    liberado_a = Column(DateTime(timezone=True), nullable=True)
    
    # Relaciones
    espacio = relationship("Espacio", back_populates="asignaciones")
    usuario = relationship("Usuario", back_populates="asignaciones")


class Incidente(Base):
    __tablename__ = "incidentes"

    id = Column(Integer, primary_key=True, index=True)
    id_de_espacio = Column(Integer, ForeignKey("espacios.id"), nullable=False)
    tipo_de_incidente = Column(String(100), nullable=False)  # ocupación sin asignar, sensor fuera de funcionamiento, etc.
    hora_de_registro = Column(DateTime(timezone=True), server_default=func.now())
    hora_de_solucion = Column(DateTime(timezone=True), nullable=True)
    nota = Column(Text, nullable=True)
    
    # Relación
    espacio = relationship("Espacio", back_populates="incidentes")
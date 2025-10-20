from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from datetime import datetime, timedelta
from typing import List, Optional
from app import models, schemas

# ============ USUARIOS ============
def create_usuario(db: Session, usuario: schemas.UsuarioCreate):
    db_usuario = models.Usuario(
        nombre=usuario.nombre,
        contraseña=usuario.contraseña  # En producción: hashear la contraseña
    )
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario(db: Session, usuario_id: int):
    return db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()

def get_usuario_by_nombre(db: Session, nombre: str):
    return db.query(models.Usuario).filter(models.Usuario.nombre == nombre).first()

def get_usuarios(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Usuario).offset(skip).limit(limit).all()

def authenticate_usuario(db: Session, nombre: str, contraseña: str):
    usuario = get_usuario_by_nombre(db, nombre)
    if not usuario or usuario.contraseña != contraseña:
        return None
    return usuario


# ============ ESPACIOS ============
def create_espacio(db: Session, espacio: schemas.EspacioCreate):
    db_espacio = models.Espacio(**espacio.model_dump())
    db.add(db_espacio)
    db.commit()
    db.refresh(db_espacio)
    return db_espacio

def get_espacio(db: Session, espacio_id: int):
    return db.query(models.Espacio).filter(models.Espacio.id == espacio_id).first()

def get_espacios(db: Session):
    return db.query(models.Espacio).order_by(models.Espacio.numero_de_espacio).all()

def get_espacios_disponibles(db: Session):
    return db.query(models.Espacio).filter(models.Espacio.estado == "libre").all()

def update_espacio_estado(db: Session, espacio_id: int, nuevo_estado: str):
    espacio = get_espacio(db, espacio_id)
    if espacio:
        espacio.estado = nuevo_estado
        db.commit()
        db.refresh(espacio)
    return espacio


# ============ ASIGNACIONES ============
def create_asignacion(db: Session, id_usuario: Optional[int] = None):
    # Buscar un espacio disponible
    espacio_disponible = db.query(models.Espacio).filter(
        models.Espacio.estado == "libre"
    ).first()
    
    if not espacio_disponible:
        return None
    
    # Crear asignación
    db_asignacion = models.Asignacion(
        id_de_espacio=espacio_disponible.id,
        id_usuario=id_usuario
    )
    
    # Actualizar estado del espacio
    espacio_disponible.estado = "ocupado"
    
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def get_asignacion(db: Session, asignacion_id: int):
    return db.query(models.Asignacion).filter(models.Asignacion.id == asignacion_id).first()

def get_asignaciones_activas(db: Session):
    return db.query(models.Asignacion).filter(
        models.Asignacion.liberado_a == None
    ).all()

def get_asignaciones_by_date_range(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    return db.query(models.Asignacion).filter(
        and_(
            models.Asignacion.asignado_a >= fecha_inicio,
            models.Asignacion.asignado_a <= fecha_fin
        )
    ).all()

def liberar_asignacion(db: Session, asignacion_id: int):
    asignacion = get_asignacion(db, asignacion_id)
    if asignacion and not asignacion.liberado_a:
        asignacion.liberado_a = datetime.now()
        
        # Liberar el espacio
        espacio = get_espacio(db, asignacion.id_de_espacio)
        if espacio:
            espacio.estado = "libre"
        
        db.commit()
        db.refresh(asignacion)
    return asignacion

def liberar_espacio(db: Session, espacio_id: int):
    # Buscar asignación activa para este espacio
    asignacion = db.query(models.Asignacion).filter(
        and_(
            models.Asignacion.id_de_espacio == espacio_id,
            models.Asignacion.liberado_a == None
        )
    ).first()
    
    if asignacion:
        asignacion.liberado_a = datetime.now()
    
    # Actualizar estado del espacio
    espacio = get_espacio(db, espacio_id)
    if espacio:
        espacio.estado = "libre"
        db.commit()
        db.refresh(espacio)
    
    return espacio


# ============ INCIDENTES ============
def create_incidente(db: Session, incidente: schemas.IncidenteCreate):
    db_incidente = models.Incidente(**incidente.model_dump())
    db.add(db_incidente)
    db.commit()
    db.refresh(db_incidente)
    return db_incidente

def get_incidente(db: Session, incidente_id: int):
    return db.query(models.Incidente).filter(models.Incidente.id == incidente_id).first()

def get_incidentes_activos(db: Session):
    return db.query(models.Incidente).filter(
        models.Incidente.hora_de_solucion == None
    ).all()

def get_incidentes_by_date_range(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    return db.query(models.Incidente).filter(
        and_(
            models.Incidente.hora_de_registro >= fecha_inicio,
            models.Incidente.hora_de_registro <= fecha_fin
        )
    ).all()

def resolver_incidente(db: Session, incidente_id: int, nota: Optional[str] = None):
    incidente = get_incidente(db, incidente_id)
    if incidente:
        incidente.hora_de_solucion = datetime.now()
        if nota:
            incidente.nota = nota
        db.commit()
        db.refresh(incidente)
    return incidente


# ============ REPORTES Y ESTADÍSTICAS ============
def get_estadisticas(db: Session, fecha_inicio: Optional[datetime] = None, fecha_fin: Optional[datetime] = None):
    # Estadísticas generales de espacios
    total_espacios = db.query(models.Espacio).count()
    espacios_disponibles = db.query(models.Espacio).filter(models.Espacio.estado == "libre").count()
    espacios_ocupados = db.query(models.Espacio).filter(models.Espacio.estado == "ocupado").count()
    espacios_reservados = db.query(models.Espacio).filter(models.Espacio.estado == "reservado").count()
    
    # Filtrar por rango de fechas si se proporciona
    query_asignaciones = db.query(models.Asignacion)
    query_incidentes = db.query(models.Incidente)
    
    if fecha_inicio and fecha_fin:
        query_asignaciones = query_asignaciones.filter(
            and_(
                models.Asignacion.asignado_a >= fecha_inicio,
                models.Asignacion.asignado_a <= fecha_fin
            )
        )
        query_incidentes = query_incidentes.filter(
            and_(
                models.Incidente.hora_de_registro >= fecha_inicio,
                models.Incidente.hora_de_registro <= fecha_fin
            )
        )
    
    total_asignaciones = query_asignaciones.count()
    total_incidentes = query_incidentes.count()
    
    # Calcular promedio de horas de ocupación
    asignaciones_completadas = query_asignaciones.filter(
        models.Asignacion.liberado_a != None
    ).all()
    
    if asignaciones_completadas:
        total_horas = sum([
            (asig.liberado_a - asig.asignado_a).total_seconds() / 3600
            for asig in asignaciones_completadas
        ])
        promedio_horas = total_horas / len(asignaciones_completadas)
    else:
        promedio_horas = 0.0
    
    return {
        "total_espacios": total_espacios,
        "espacios_disponibles": espacios_disponibles,
        "espacios_ocupados": espacios_ocupados,
        "espacios_reservados": espacios_reservados,
        "total_asignaciones": total_asignaciones,
        "total_incidentes": total_incidentes,
        "promedio_horas_ocupacion": round(promedio_horas, 2)
    }
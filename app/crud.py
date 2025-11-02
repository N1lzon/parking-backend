from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from typing import List, Optional
from app import models, schemas

# ============ ADMIN ============
def create_admin(db: Session, admin: schemas.AdminCreate):
    db_admin = models.Admin(
        nombre=admin.nombre,
        contraseña=admin.contraseña  # En producción: hashear la contraseña
    )
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    return db_admin

def get_admin(db: Session, admin_id: int):
    return db.query(models.Admin).filter(models.Admin.id == admin_id).first()

def get_admin_by_nombre(db: Session, nombre: str):
    return db.query(models.Admin).filter(models.Admin.nombre == nombre).first()

def get_admins(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Admin).offset(skip).limit(limit).all()

def authenticate_admin(db: Session, nombre: str, contraseña: str):
    admin = get_admin_by_nombre(db, nombre)
    if not admin or admin.contraseña != contraseña:
        return None
    return admin


# ============ USUARIOS RESERVA ============
def create_usuario_reserva(db: Session, usuario: schemas.UsuarioReservaCreate):
    db_usuario = models.UsuarioReserva(**usuario.model_dump())
    db.add(db_usuario)
    db.commit()
    db.refresh(db_usuario)
    return db_usuario

def get_usuario_reserva(db: Session, ci: int):
    return db.query(models.UsuarioReserva).filter(models.UsuarioReserva.ci == ci).first()

def get_usuarios_reserva(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.UsuarioReserva).offset(skip).limit(limit).all()

def update_usuario_reserva(db: Session, ci: int, usuario_update: schemas.UsuarioReservaUpdate):
    usuario = get_usuario_reserva(db, ci)
    if usuario:
        if usuario_update.nombre:
            usuario.nombre = usuario_update.nombre
        db.commit()
        db.refresh(usuario)
    return usuario

def delete_usuario_reserva(db: Session, ci: int):
    usuario = get_usuario_reserva(db, ci)
    if usuario:
        db.delete(usuario)
        db.commit()
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

def get_espacio_by_numero(db: Session, numero: int):
    return db.query(models.Espacio).filter(models.Espacio.numero_de_espacio == numero).first()

def get_espacios(db: Session):
    return db.query(models.Espacio).order_by(models.Espacio.numero_de_espacio).all()

def get_espacios_disponibles(db: Session, solo_no_reservados: bool = False):
    """
    Obtener espacios disponibles.
    Si solo_no_reservados=True, solo devuelve espacios libres y no reservados (para usuarios normales)
    Si solo_no_reservados=False, devuelve todos los espacios libres
    """
    query = db.query(models.Espacio).filter(models.Espacio.estado == "libre")
    if solo_no_reservados:
        query = query.filter(models.Espacio.reservado == "no")
    return query.all()

def update_espacio(db: Session, espacio_id: int, espacio_update: schemas.EspacioUpdate):
    espacio = get_espacio(db, espacio_id)
    if espacio:
        if espacio_update.estado:
            espacio.estado = espacio_update.estado
        if espacio_update.reservado:
            espacio.reservado = espacio_update.reservado
        db.commit()
        db.refresh(espacio)
    return espacio


# ============ ASIGNACIONES ============
def create_asignacion(db: Session, ci: Optional[int] = None):
    """
    Crear una nueva asignación de espacio.
    - Si ci es None: usuario normal, buscar espacio libre NO reservado
    - Si ci tiene valor: usuario con reserva, buscar espacio libre RESERVADO
    """
    
    if ci:
        # Usuario con reserva
        usuario = get_usuario_reserva(db, ci)
        if not usuario:
            return None  # Usuario no existe en tabla de reservas
        
        # Buscar espacio libre y reservado
        espacio_disponible = db.query(models.Espacio).filter(
            and_(
                models.Espacio.estado == "libre",
                models.Espacio.reservado == "si"
            )
        ).first()
        
        if not espacio_disponible:
            return None  # No hay espacios reservados disponibles
        
        # Crear asignación con CI
        db_asignacion = models.Asignacion(
            ci_reserva=ci,
            id_de_espacio=espacio_disponible.id
        )
        
    else:
        # Usuario normal
        # Buscar espacio libre y NO reservado
        espacio_disponible = db.query(models.Espacio).filter(
            and_(
                models.Espacio.estado == "libre",
                models.Espacio.reservado == "no"
            )
        ).first()
        
        if not espacio_disponible:
            return None  # No hay espacios disponibles
        
        # Crear asignación sin CI
        db_asignacion = models.Asignacion(
            ci_reserva=None,
            id_de_espacio=espacio_disponible.id
        )
    
    # Actualizar estado del espacio a ocupado
    espacio_disponible.estado = "ocupado"
    
    db.add(db_asignacion)
    db.commit()
    db.refresh(db_asignacion)
    return db_asignacion

def get_asignacion(db: Session, asignacion_id: int):
    return db.query(models.Asignacion).filter(models.Asignacion.id == asignacion_id).first()

def get_asignaciones_activas(db: Session):
    return db.query(models.Asignacion).filter(
        models.Asignacion.hora_liberado == None
    ).all()

def get_asignaciones_by_date_range(db: Session, fecha_inicio: datetime, fecha_fin: datetime):
    return db.query(models.Asignacion).filter(
        and_(
            models.Asignacion.hora_asignado >= fecha_inicio,
            models.Asignacion.hora_asignado <= fecha_fin
        )
    ).all()

def liberar_asignacion(db: Session, asignacion_id: int):
    asignacion = get_asignacion(db, asignacion_id)
    if asignacion and not asignacion.hora_liberado:
        asignacion.hora_liberado = datetime.now()
        
        # Liberar el espacio (cambiar estado a libre, mantener reservado como está)
        espacio = get_espacio(db, asignacion.id_de_espacio)
        if espacio:
            espacio.estado = "libre"
        
        db.commit()
        db.refresh(asignacion)
    return asignacion

def liberar_espacio(db: Session, espacio_id: int):
    """Liberar un espacio directamente (simula sensor detectando salida)"""
    # Buscar asignación activa para este espacio
    asignacion = db.query(models.Asignacion).filter(
        and_(
            models.Asignacion.id_de_espacio == espacio_id,
            models.Asignacion.hora_liberado == None
        )
    ).first()
    
    if asignacion:
        asignacion.hora_liberado = datetime.now()
    
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
    espacios_reservados = db.query(models.Espacio).filter(models.Espacio.reservado == "si").count()
    
    # Filtrar por rango de fechas si se proporciona
    query_asignaciones = db.query(models.Asignacion)
    query_incidentes = db.query(models.Incidente)
    
    if fecha_inicio and fecha_fin:
        query_asignaciones = query_asignaciones.filter(
            and_(
                models.Asignacion.hora_asignado >= fecha_inicio,
                models.Asignacion.hora_asignado <= fecha_fin
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
        models.Asignacion.hora_liberado != None
    ).all()
    
    if asignaciones_completadas:
        total_horas = sum([
            (asig.hora_liberado - asig.hora_asignado).total_seconds() / 3600
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
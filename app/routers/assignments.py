from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app import crud, schemas, models
from app.database import get_db

router = APIRouter(
    prefix="/asignaciones",
    tags=["Asignaciones"]
)

# ============================================================
# FUNCIÓN AUXILIAR: Verificar si estacionamiento está lleno
# ============================================================

def verificar_y_registrar_estado_estacionamiento(db: Session):
    """
    Verifica si el estacionamiento está lleno y registra/resuelve incidentes automáticamente.
    
    - Si se llena: crea incidente tipo "estacionamiento_lleno"
    - Si deja de estar lleno: resuelve el incidente activo
    """
    try:
        # Obtener todos los espacios
        espacios = db.query(models.Espacio).all()
        total_espacios = len(espacios)
        
        if total_espacios == 0:
            return
        
        espacios_reservados = len([e for e in espacios if e.reservado == 'si'])
        espacios_no_reservados = total_espacios - espacios_reservados
        espacios_ocupados = len([e for e in espacios if e.estado == 'ocupado'])
        
        esta_lleno = espacios_ocupados >= espacios_no_reservados
        
        # Buscar si ya hay un incidente activo de "estacionamiento_lleno"
        incidente_activo = db.query(models.Incidente).filter(
            models.Incidente.tipo_de_incidente == "estacionamiento_lleno",
            models.Incidente.hora_de_solucion == None
        ).first()
        
        if esta_lleno and not incidente_activo:
            # El estacionamiento se acaba de llenar - CREAR INCIDENTE
            # Usar espacio ID 1 como referencia (es un evento general, no específico de un espacio)
            nuevo_incidente = models.Incidente(
                id_de_espacio=1,  # ID genérico
                tipo_de_incidente="estacionamiento_lleno",
                nota=f"Estacionamiento lleno: {espacios_ocupados}/{espacios_no_reservados} espacios no reservados ocupados",
                hora_de_registro=datetime.now()
            )
            db.add(nuevo_incidente)
            db.commit()
            print(f"🔥 INCIDENTE CREADO: Estacionamiento lleno ({espacios_ocupados}/{espacios_no_reservados})")
            
        elif not esta_lleno and incidente_activo:
            # El estacionamiento dejó de estar lleno - RESOLVER INCIDENTE
            incidente_activo.hora_de_solucion = datetime.now()
            if not incidente_activo.nota:
                incidente_activo.nota = ""
            incidente_activo.nota += f"\nResuelto automáticamente: espacio disponible ({espacios_ocupados}/{espacios_no_reservados})"
            db.commit()
            print(f"✅ INCIDENTE RESUELTO: Estacionamiento ya no está lleno ({espacios_ocupados}/{espacios_no_reservados})")
    
    except Exception as e:
        print(f"⚠️ Error en verificar_y_registrar_estado_estacionamiento: {e}")
        # No lanzar excepción para no interrumpir el flujo principal

# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/solicitar", response_model=schemas.AsignacionResponse)
def solicitar_espacio(asignacion: schemas.AsignacionCreate, db: Session = Depends(get_db)):
    """
    Solicitar un espacio de estacionamiento.
    - Si ci es None, es un usuario normal (anónimo).
    - Si ci tiene valor, busca la reserva asociada.
    
    Este endpoint es usado por el User Interface (pantalla táctil).
    """
    # Verificar si hay espacios disponibles ANTES de intentar asignar
    if asignacion.ci:
        # Usuario con reserva - buscar espacio reservado disponible
        espacio_disponible = db.query(models.Espacio).filter(
            models.Espacio.estado == "libre",
            models.Espacio.reservado == "si"
        ).first()
    else:
        # Usuario normal - buscar espacio no reservado disponible
        espacio_disponible = db.query(models.Espacio).filter(
            models.Espacio.estado == "libre",
            models.Espacio.reservado == "no"
        ).first()
    
    # Si NO hay espacios disponibles, registrar rechazo
    if not espacio_disponible:
        # Registrar incidente de solicitud rechazada
        incidente_rechazo = models.Incidente(
            id_de_espacio=1,  # ID genérico
            tipo_de_incidente="solicitud_rechazada",
            nota=f"Solicitud rechazada - CI: {asignacion.ci if asignacion.ci else 'Usuario anónimo'} - Sin espacios {'reservados' if asignacion.ci else 'no reservados'} disponibles",
            hora_de_registro=datetime.now(),
            hora_de_solucion=datetime.now()  # Auto-resuelto (es un evento puntual)
        )
        db.add(incidente_rechazo)
        db.commit()
        print(f"🚫 SOLICITUD RECHAZADA registrada: CI={asignacion.ci}")
        
        # Lanzar excepción al usuario
        if asignacion.ci:
            raise HTTPException(status_code=404, detail="No se encontró la reserva o no hay espacios reservados disponibles")
        else:
            raise HTTPException(status_code=404, detail="No hay espacios disponibles")
    
    # HAY espacio disponible - crear asignación
    db_asignacion = crud.create_asignacion(db=db, ci=asignacion.ci)
    
    if not db_asignacion:
        raise HTTPException(status_code=500, detail="Error al crear la asignación")
    
    # Verificar si el estacionamiento se llenó con esta asignación
    verificar_y_registrar_estado_estacionamiento(db)
    
    return db_asignacion

@router.post("/", response_model=schemas.AsignacionResponse)
def create_asignacion(asignacion: schemas.AsignacionCreate, db: Session = Depends(get_db)):
    """
    Solicitar un espacio de estacionamiento.
    - Si ci es None, es un usuario normal (anónimo).
    - Si ci tiene valor, busca la reserva asociada.
    """
    # Reutilizar la lógica de /solicitar
    return solicitar_espacio(asignacion, db)

@router.get("/activas", response_model=List[schemas.AsignacionResponse])
def get_asignaciones_activas(db: Session = Depends(get_db)):
    """Obtener todas las asignaciones activas (no liberadas)"""
    return crud.get_asignaciones_activas(db=db)

@router.get("/{asignacion_id}", response_model=schemas.AsignacionResponse)
def get_asignacion(asignacion_id: int, db: Session = Depends(get_db)):
    """Obtener una asignación específica"""
    asignacion = crud.get_asignacion(db=db, asignacion_id=asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    return asignacion

@router.put("/{asignacion_id}/liberar", response_model=schemas.AsignacionResponse)
def liberar_asignacion(asignacion_id: int, db: Session = Depends(get_db)):
    """Liberar una asignación (marcar salida del vehículo)"""
    asignacion = crud.liberar_asignacion(db=db, asignacion_id=asignacion_id)
    if not asignacion:
        raise HTTPException(status_code=404, detail="Asignación no encontrada")
    
    # Verificar si el estacionamiento dejó de estar lleno con esta liberación
    verificar_y_registrar_estado_estacionamiento(db)
    
    return asignacion

@router.put("/espacio/{espacio_id}/liberar", response_model=schemas.EspacioResponse)
def liberar_espacio(espacio_id: int, db: Session = Depends(get_db)):
    """Liberar un espacio directamente (simula sensor detectando salida)"""
    espacio = crud.liberar_espacio(db=db, espacio_id=espacio_id)
    if not espacio:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    
    # Verificar si el estacionamiento dejó de estar lleno con esta liberación
    verificar_y_registrar_estado_estacionamiento(db)
    
    return espacio
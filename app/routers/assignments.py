from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/asignaciones",
    tags=["Asignaciones"]
)

@router.post("/", response_model=schemas.AsignacionResponse)
def create_asignacion(asignacion: schemas.AsignacionCreate, db: Session = Depends(get_db)):
    """
    Solicitar un espacio de estacionamiento.
    - Si ci es None, es un usuario normal (anónimo).
    - Si ci tiene valor, busca la reserva asociada.
    """
    db_asignacion = crud.create_asignacion(db=db, ci=asignacion.ci)
    if not db_asignacion:
        if asignacion.ci:
            raise HTTPException(status_code=404, detail="No se encontró la reserva o no hay espacios disponibles")
        else:
            raise HTTPException(status_code=404, detail="No hay espacios disponibles")
    return db_asignacion

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
    return asignacion

@router.put("/espacio/{espacio_id}/liberar", response_model=schemas.EspacioResponse)
def liberar_espacio(espacio_id: int, db: Session = Depends(get_db)):
    """Liberar un espacio directamente (simula sensor detectando salida)"""
    espacio = crud.liberar_espacio(db=db, espacio_id=espacio_id)
    if not espacio:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return espacio
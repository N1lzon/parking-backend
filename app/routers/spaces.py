from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/espacios",
    tags=["Espacios"]
)

@router.post("/", response_model=schemas.EspacioResponse)
def create_espacio(espacio: schemas.EspacioCreate, db: Session = Depends(get_db)):
    """Crear un nuevo espacio de estacionamiento"""
    return crud.create_espacio(db=db, espacio=espacio)

@router.get("/", response_model=List[schemas.EspacioResponse])
def get_espacios(db: Session = Depends(get_db)):
    """Obtener todos los espacios"""
    return crud.get_espacios(db=db)

@router.get("/disponibles", response_model=List[schemas.EspacioResponse])
def get_espacios_disponibles(db: Session = Depends(get_db)):
    """Obtener solo espacios disponibles"""
    return crud.get_espacios_disponibles(db=db)

@router.get("/{espacio_id}", response_model=schemas.EspacioResponse)
def get_espacio(espacio_id: int, db: Session = Depends(get_db)):
    """Obtener un espacio específico"""
    espacio = crud.get_espacio(db=db, espacio_id=espacio_id)
    if not espacio:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return espacio

@router.put("/{espacio_id}", response_model=schemas.EspacioResponse)
def update_espacio(espacio_id: int, espacio_update: schemas.EspacioUpdate, db: Session = Depends(get_db)):
    """Actualizar el estado de un espacio"""
    espacio = crud.update_espacio_estado(db=db, espacio_id=espacio_id, nuevo_estado=espacio_update.estado)
    if not espacio:
        raise HTTPException(status_code=404, detail="Espacio no encontrado")
    return espacio
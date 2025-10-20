from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/incidentes",
    tags=["Incidentes"]
)

@router.post("/", response_model=schemas.IncidenteResponse)
def create_incidente(incidente: schemas.IncidenteCreate, db: Session = Depends(get_db)):
    """Registrar un nuevo incidente"""
    return crud.create_incidente(db=db, incidente=incidente)

@router.get("/activos", response_model=List[schemas.IncidenteResponse])
def get_incidentes_activos(db: Session = Depends(get_db)):
    """Obtener incidentes no resueltos"""
    return crud.get_incidentes_activos(db=db)

@router.get("/{incidente_id}", response_model=schemas.IncidenteResponse)
def get_incidente(incidente_id: int, db: Session = Depends(get_db)):
    """Obtener un incidente específico"""
    incidente = crud.get_incidente(db=db, incidente_id=incidente_id)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return incidente

@router.put("/{incidente_id}/resolver", response_model=schemas.IncidenteResponse)
def resolver_incidente(incidente_id: int, update: schemas.IncidenteUpdate, db: Session = Depends(get_db)):
    """Marcar un incidente como resuelto"""
    incidente = crud.resolver_incidente(db=db, incidente_id=incidente_id, nota=update.nota)
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    return incidente
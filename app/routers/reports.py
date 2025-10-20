from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"]
)

@router.post("/estadisticas", response_model=schemas.EstadisticasResponse)
def get_estadisticas(reporte: schemas.ReporteRequest, db: Session = Depends(get_db)):
    """
    Obtener estadísticas del estacionamiento en un rango de fechas.
    Incluye: total de espacios, disponibles, ocupados, reservados,
    total de asignaciones, incidentes y promedio de horas de ocupación.
    """
    estadisticas = crud.get_estadisticas(
        db=db,
        fecha_inicio=reporte.fecha_inicio,
        fecha_fin=reporte.fecha_fin
    )
    return estadisticas

@router.get("/estadisticas/actual", response_model=schemas.EstadisticasResponse)
def get_estadisticas_actuales(db: Session = Depends(get_db)):
    """Obtener estadísticas generales sin filtro de fechas"""
    estadisticas = crud.get_estadisticas(db=db)
    return estadisticas

@router.post("/asignaciones", response_model=List[schemas.AsignacionResponse])
def get_reporte_asignaciones(reporte: schemas.ReporteRequest, db: Session = Depends(get_db)):
    """Obtener todas las asignaciones en un rango de fechas"""
    return crud.get_asignaciones_by_date_range(
        db=db,
        fecha_inicio=reporte.fecha_inicio,
        fecha_fin=reporte.fecha_fin
    )

@router.post("/incidentes", response_model=List[schemas.IncidenteResponse])
def get_reporte_incidentes(reporte: schemas.ReporteRequest, db: Session = Depends(get_db)):
    """Obtener todos los incidentes en un rango de fechas"""
    return crud.get_incidentes_by_date_range(
        db=db,
        fecha_inicio=reporte.fecha_inicio,
        fecha_fin=reporte.fecha_fin
    )
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/usuarios-reserva",
    tags=["Usuarios Reserva"]
)

@router.post("/", response_model=schemas.UsuarioReservaResponse)
def create_usuario_reserva(usuario: schemas.UsuarioReservaCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario con derecho a reserva"""
    # Verificar si el CI ya existe
    db_usuario = crud.get_usuario_reserva(db, ci=usuario.ci)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Ya existe un usuario con este CI")
    return crud.create_usuario_reserva(db=db, usuario=usuario)

@router.get("/", response_model=List[schemas.UsuarioReservaResponse])
def get_usuarios_reserva(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener todos los usuarios con derecho a reserva"""
    return crud.get_usuarios_reserva(db=db, skip=skip, limit=limit)

@router.get("/{ci}", response_model=schemas.UsuarioReservaResponse)
def get_usuario_reserva(ci: int, db: Session = Depends(get_db)):
    """Obtener un usuario con reserva por CI"""
    usuario = crud.get_usuario_reserva(db=db, ci=ci)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.put("/{ci}", response_model=schemas.UsuarioReservaResponse)
def update_usuario_reserva(ci: int, usuario_update: schemas.UsuarioReservaUpdate, db: Session = Depends(get_db)):
    """Actualizar un usuario con reserva"""
    usuario = crud.update_usuario_reserva(db=db, ci=ci, usuario_update=usuario_update)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.delete("/{ci}")
def delete_usuario_reserva(ci: int, db: Session = Depends(get_db)):
    """Eliminar un usuario con reserva"""
    usuario = crud.delete_usuario_reserva(db=db, ci=ci)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return {"message": "Usuario eliminado exitosamente"}
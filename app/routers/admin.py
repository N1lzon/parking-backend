from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.delete("/{admin_id}")
def delete_admin(admin_id: int, db: Session = Depends(get_db)):
    db_admin = crud.delete_admin(db, admin_id)
    if not db_admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return {"message": "Administrador eliminado exitosamente"}

@router.post("/", response_model=schemas.AdminResponse)
def create_admin(admin: schemas.AdminCreate, db: Session = Depends(get_db)):
    """Crear un nuevo administrador"""
    # Verificar si el administrador ya existe
    db_admin = crud.get_admin_by_nombre(db, nombre=admin.nombre)
    if db_admin:
        raise HTTPException(status_code=400, detail="Administrador ya registrado")
    return crud.create_admin(db=db, admin=admin)

@router.get("/", response_model=List[schemas.AdminResponse])
def get_admins(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener todos los administradores"""
    return crud.get_admins(db=db, skip=skip, limit=limit)

@router.get("/{admin_id}", response_model=schemas.AdminResponse)
def get_admin(admin_id: int, db: Session = Depends(get_db)):
    """Obtener un administrador específico"""
    admin = crud.get_admin(db=db, admin_id=admin_id)
    if not admin:
        raise HTTPException(status_code=404, detail="Administrador no encontrado")
    return admin

@router.post("/login", response_model=schemas.AdminResponse)
def login_admin(login: schemas.AdminLogin, db: Session = Depends(get_db)):
    """Autenticar un administrador"""
    admin = crud.authenticate_admin(db=db, nombre=login.nombre, contraseña=login.contraseña)
    if not admin:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return admin

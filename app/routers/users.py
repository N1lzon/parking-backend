from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app import crud, schemas
from app.database import get_db

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)

@router.post("/", response_model=schemas.UsuarioResponse)
def create_usuario(usuario: schemas.UsuarioCreate, db: Session = Depends(get_db)):
    """Crear un nuevo usuario especial"""
    # Verificar si el usuario ya existe
    db_usuario = crud.get_usuario_by_nombre(db, nombre=usuario.nombre)
    if db_usuario:
        raise HTTPException(status_code=400, detail="Usuario ya registrado")
    return crud.create_usuario(db=db, usuario=usuario)

@router.get("/", response_model=List[schemas.UsuarioResponse])
def get_usuarios(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Obtener todos los usuarios"""
    return crud.get_usuarios(db=db, skip=skip, limit=limit)

@router.get("/{usuario_id}", response_model=schemas.UsuarioResponse)
def get_usuario(usuario_id: int, db: Session = Depends(get_db)):
    """Obtener un usuario específico"""
    usuario = crud.get_usuario(db=db, usuario_id=usuario_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return usuario

@router.post("/login", response_model=schemas.UsuarioResponse)
def login_usuario(login: schemas.UsuarioLogin, db: Session = Depends(get_db)):
    """Autenticar un usuario especial"""
    usuario = crud.authenticate_usuario(db=db, nombre=login.nombre, contraseña=login.contraseña)
    if not usuario:
        raise HTTPException(status_code=401, detail="Credenciales incorrectas")
    return usuario
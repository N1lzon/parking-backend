from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import spaces, admin, usuarios_reserva, assignments, incidents, reports, websocket

# Crear las tablas en la base de datos
Base.metadata.create_all(bind=engine)

# Crear la aplicación FastAPI
app = FastAPI(
    title="Sistema de Gestión de Estacionamiento",
    description="API para gestionar espacios de estacionamiento, asignaciones y reportes",
    version="1.0.0"
)

# Configurar CORS para permitir conexiones desde el frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especificar los orígenes permitidos
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir routers
app.include_router(spaces.router)
app.include_router(admin.router)
app.include_router(usuarios_reserva.router)
app.include_router(assignments.router)
app.include_router(incidents.router)
app.include_router(reports.router)
app.include_router(websocket.router)

@app.get("/")
def read_root():
    return {
        "message": "API de Gestión de Estacionamiento",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "ok"}
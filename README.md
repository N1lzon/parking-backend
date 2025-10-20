# Sistema de Gestión de Estacionamiento - Backend

API REST desarrollada con FastAPI para gestionar espacios de estacionamiento.

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

## 🚀 Instalación

### 1. Crear y activar entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Inicializar la base de datos

```bash
python init_db.py
```

Este script creará:
- 20 espacios de estacionamiento (numerados del 01 al 20)
- 3 usuarios de ejemplo con sus credenciales

## ▶️ Ejecutar el Servidor

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: `http://localhost:8000`

## 📚 Documentación de la API

Una vez que el servidor esté ejecutándose, puedes acceder a:

- **Swagger UI (interactivo):** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

## 🔑 Usuarios de Prueba

| Usuario | Contraseña |
|---------|-----------|
| admin | admin123 |
| juan.perez | 1234 |
| maria.gomez | 5678 |

## 📡 Endpoints Principales

### Espacios
- `GET /espacios` - Listar todos los espacios
- `GET /espacios/disponibles` - Listar espacios disponibles
- `POST /espacios` - Crear nuevo espacio
- `PUT /espacios/{id}` - Actualizar estado de espacio

### Usuarios
- `POST /usuarios` - Crear usuario especial
- `POST /usuarios/login` - Autenticar usuario
- `GET /usuarios` - Listar usuarios

### Asignaciones
- `POST /asignaciones` - Solicitar espacio (asignar automáticamente)
- `GET /asignaciones/activas` - Listar asignaciones activas
- `PUT /asignaciones/{id}/liberar` - Liberar asignación
- `PUT /asignaciones/espacio/{id}/liberar` - Liberar espacio directamente

### Incidentes
- `POST /incidentes` - Registrar incidente
- `GET /incidentes/activos` - Listar incidentes no resueltos
- `PUT /incidentes/{id}/resolver` - Resolver incidente

### Reportes
- `GET /reportes/estadisticas/actual` - Estadísticas actuales
- `POST /reportes/estadisticas` - Estadísticas por rango de fechas
- `POST /reportes/asignaciones` - Reporte de asignaciones
- `POST /reportes/incidentes` - Reporte de incidentes

### WebSocket
- `WS /ws` - Conexión WebSocket para actualizaciones en tiempo real

## 🧪 Probar la API

### Ejemplo 1: Solicitar un espacio
```bash
curl -X POST "http://localhost:8000/asignaciones/" \
  -H "Content-Type: application/json" \
  -d '{"id_usuario": null}'
```

### Ejemplo 2: Ver todos los espacios
```bash
curl -X GET "http://localhost:8000/espacios/"
```

### Ejemplo 3: Login de usuario
```bash
curl -X POST "http://localhost:8000/usuarios/login" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "admin", "contraseña": "admin123"}'
```

### Ejemplo 4: Obtener estadísticas
```bash
curl -X GET "http://localhost:8000/reportes/estadisticas/actual"
```

## 🗂️ Estructura del Proyecto

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Aplicación principal
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Esquemas Pydantic
│   ├── database.py          # Configuración de BD
│   ├── crud.py              # Operaciones de BD
│   └── routers/
│       ├── spaces.py        # Endpoints de espacios
│       ├── users.py         # Endpoints de usuarios
│       ├── assignments.py   # Endpoints de asignaciones
│       ├── incidents.py     # Endpoints de incidentes
│       ├── reports.py       # Endpoints de reportes
│       └── websocket.py     # WebSocket
├── init_db.py               # Script de inicialización
├── requirements.txt         # Dependencias
├── parking.db              # Base de datos SQLite (se crea al inicializar)
└── README.md
```

## 🔧 Solución de Problemas

### Error: "No module named 'app'"
Asegúrate de estar en la carpeta `backend` al ejecutar uvicorn.

### Error: "Database is locked"
Cierra cualquier aplicación que esté usando la base de datos (como DB Browser).

### El servidor no inicia
Verifica que el puerto 8000 no esté en uso:
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

## 📝 Notas

- La base de datos es SQLite y se almacena en `parking.db`
- Las contraseñas NO están hasheadas en este prototipo (para producción, usar bcrypt)
- El WebSocket permite actualizaciones en tiempo real al frontend
- CORS está configurado para permitir cualquier origen (ajustar en producción)

## 🔜 Próximos Pasos

1. Crear el frontend con React
2. Conectar ambas interfaces (Usuario y Administrador)
3. Implementar autenticación con JWT
4. Añadir integración con sensores físicos
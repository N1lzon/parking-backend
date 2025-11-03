
# Sistema de Gestión de Estacionamiento - Backend

Este es el repositorio para el backend de un sistema de gestión de estacionamiento, usando FastAPI para la gestión completa de un sistema de estacionamiento inteligente.



## Autores

- [Nilson Casco](https://www.github.com/octokatherine)
- [Juan Ovelar](https://github.com/JoMaiky)
- [Thamara Villalba](https://github.com/Th4mx)


##  📁 Estructura del Proyecto

```bash
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # Punto de entrada de la aplicación
│   ├── database.py          # Configuración de la base de datos
│   ├── models.py            # Modelos SQLAlchemy
│   ├── schemas.py           # Esquemas Pydantic para validación
│   ├── crud.py              # Operaciones CRUD
│   └── routers/
│       ├── admin.py             # Endpoints de administradores
│       ├── usuarios_reserva.py  # Endpoints de usuarios con reserva
│       ├── spaces.py            # Endpoints de espacios
│       ├── assignments.py       # Endpoints de asignaciones
│       ├── incidents.py         # Endpoints de incidentes
│       ├── reports.py           # Endpoints de reportes
│       └── websocket.py         # WebSocket para tiempo real
├── init_db.py               # Script de inicialización
├── requirements.txt         # Dependencias del proyecto
├── parking.db               # Base de datos SQLite (generada automáticamente)
└── README.md
```

## Modelos de Datos
### 👨‍💼 Admin

Administradores del sistema con acceso al panel de control.

| Campo          | Tipo         | Descripción                        |
| -------------- | ------------ | ---------------------------------- |
| **id**         | Integer (PK) | Identificador único                |
| **nombre**     | String       | Nombre de usuario                  |
| **contraseña** | String       | Contraseña (sin hash en prototipo) |

### 👤 UsuarioReserva

Usuarios autorizados para usar espacios reservados (docentes/empleados).

| Campo      | Tipo         | Descripción         |
| ---------- | ------------ | ------------------- |
| **ci**     | Integer (PK) | Cédula de identidad |
| **nombre** | String       | Nombre completo     |

### 🅿️ Espacio

Espacios físicos de estacionamiento.

| Campo                 | Tipo         | Descripción                            |
| --------------------- | ------------ | -------------------------------------- |
| **id**                | Integer (PK) | Identificador único                    |
| **numero_de_espacio** | Integer      | Número visible del espacio (1–20)      |
| **estado**            | String       | Estado actual: `"libre"` u `"ocupado"` |
| **reservado**         | String       | Tipo de espacio: `"si"` o `"no"`       |

### 🚗 Asignacion

Registro de asignaciones de espacios a vehículos.

| Campo             | Tipo         | Descripción                                |
| ----------------- | ------------ | ------------------------------------------ |
| **id**            | Integer (PK) | Identificador único                        |
| **ci_reserva**    | Integer (FK) | CI del usuario (null si es usuario normal) |
| **id_de_espacio** | Integer (FK) | ID del espacio asignado                    |
| **hora_asignado** | DateTime     | Timestamp de entrada                       |
| **hora_liberado** | DateTime     | Timestamp de salida (null si activo)       |

### ⚠️ Incidente

Registro de incidentes en el estacionamiento.

| Campo                 | Tipo         | Descripción                              |
| --------------------- | ------------ | ---------------------------------------- |
| **id**                | Integer (PK) | Identificador único                      |
| **id_de_espacio**     | Integer (FK) | Espacio relacionado                      |
| **tipo_de_incidente** | String       | Tipo: `"ocupación sin asignar"`, etc.    |
| **hora_de_registro**  | DateTime     | Timestamp del incidente                  |
| **hora_de_solucion**  | DateTime     | Timestamp de resolución (null si activo) |
| **nota**              | Text         | Descripción opcional                     |

## 🚀 Endpoints de la API

---

### 🔐 **Admin** — `/admin`

#### **POST** `/admin/login`

Autenticar un administrador.

**Body:**

```json
{
  "nombre": "admin",
  "contraseña": "admin123"
}
```

**Response (200):**

```json
{
  "id": 1,
  "nombre": "admin"
}
```

**Errores:**

* 401: Credenciales incorrectas

---

#### **POST** `/admin/`

Crear un nuevo administrador.

**Body:**

```json
{
  "nombre": "nuevo_admin",
  "contraseña": "password123"
}
```

**Response (200):**

```json
{
  "id": 3,
  "nombre": "nuevo_admin"
}
```

**Errores:**

* 400: Administrador ya existe

---

#### **GET** `/admin/`

Obtener lista de administradores.

**Query Params:**

* `skip`: Número de registros a omitir (default: 0)
* `limit`: Máximo de registros a retornar (default: 100)

**Response (200):**

```json
[
  { "id": 1, "nombre": "admin" },
  { "id": 2, "nombre": "supervisor" }
]
```

---

### 👥 **Usuarios Reserva** — `/usuarios-reserva`

#### **GET** `/usuarios-reserva/{ci}`

Verificar si un CI tiene derecho a reserva.

**Response (200):**

```json
{
  "ci": 12345678,
  "nombre": "Juan Pérez"
}
```

**Errores:**

* 404: Usuario no encontrado

---

#### **POST** `/usuarios-reserva/`

Registrar un nuevo usuario con derecho a reserva.

**Body:**

```json
{
  "ci": 99887766,
  "nombre": "Pedro Gómez"
}
```

**Response (200):**

```json
{
  "ci": 99887766,
  "nombre": "Pedro Gómez"
}
```

**Errores:**

* 400: Ya existe un usuario con ese CI

---

#### **GET** `/usuarios-reserva/`

Listar todos los usuarios con derecho a reserva.

**Response (200):**

```json
[
  { "ci": 12345678, "nombre": "Juan Pérez" },
  { "ci": 87654321, "nombre": "María Gómez" }
]
```

---

#### **PUT** `/usuarios-reserva/{ci}`

Actualizar datos de un usuario con reserva.

**Body:**

```json
{ "nombre": "Juan Carlos Pérez" }
```

**Response (200):**

```json
{
  "ci": 12345678,
  "nombre": "Juan Carlos Pérez"
}
```

---

#### **DELETE** `/usuarios-reserva/{ci}`

Eliminar un usuario con derecho a reserva.

**Response (200):**

```json
{ "message": "Usuario eliminado exitosamente" }
```

---

### 🅿️ **Espacios** — `/espacios`

#### **GET** `/espacios/`

Obtener todos los espacios del estacionamiento.

#### **GET** `/espacios/disponibles`

Obtener solo espacios libres.

#### **GET** `/espacios/{espacio_id}`

Obtener un espacio específico.
**Errores:**

* 404: Espacio no encontrado

#### **POST** `/espacios/`

Crear un nuevo espacio (uso administrativo).

#### **PUT** `/espacios/{espacio_id}`

Actualizar un espacio (cambiar estado o reservado).

*(Todas las respuestas siguen el mismo formato JSON de espacio)*

---

### 🚗 **Asignaciones** — `/asignaciones`

#### **POST** `/asignaciones/`

Solicitar un espacio de estacionamiento.

* Si `ci` es null → asigna espacio **no reservado**.
* Si `ci` tiene valor → asigna espacio **reservado**.

#### **GET** `/asignaciones/activas`

Obtener todas las asignaciones activas.

#### **GET** `/asignaciones/{asignacion_id}`

Obtener detalles de una asignación específica.

#### **PUT** `/asignaciones/{asignacion_id}/liberar`

Marcar salida de un vehículo.

#### **PUT** `/asignaciones/espacio/{espacio_id}/liberar`

Liberar un espacio directamente (simulación de sensor).

---

### 🚨 **Incidentes** — `/incidentes`

#### **POST** `/incidentes/`

Registrar un nuevo incidente.

#### **GET** `/incidentes/activos`

Obtener incidentes no resueltos.

#### **GET** `/incidentes/{incidente_id}`

Obtener detalles de un incidente.

#### **PUT** `/incidentes/{incidente_id}/resolver`

Marcar un incidente como resuelto.

---

### 📊 **Reportes** — `/reportes`

#### **GET** `/reportes/estadisticas/actual`

Obtener estadísticas generales del sistema.

#### **POST** `/reportes/estadisticas`

Obtener estadísticas en un rango de fechas.

#### **POST** `/reportes/asignaciones`

Obtener asignaciones en un rango de fechas.

#### **POST** `/reportes/incidentes`

Obtener incidentes en un rango de fechas.

---

### 🔌 **WebSocket** — `/ws`

Conexión WebSocket para actualizaciones en tiempo real.
**URL:** `ws://localhost:8000/ws`

**Eventos emitidos:**

```json
{
  "type": "espacio_update",
  "data": { "espacio_id": 5, "estado": "ocupado" }
}
```

```json
{
  "type": "nueva_asignacion",
  "data": { "asignacion_id": 20, "espacio_id": 8 }
}
```

```json
{
  "type": "nuevo_incidente",
  "data": { "incidente_id": 9, "espacio_id": 12 }
}
```

---




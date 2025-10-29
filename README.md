# Parking Backend 🚗

Este es el repositorio para el backend de un sistema de gestión de estacionamiento. La API RESTful permite manejar usuarios, lugares de estacionamiento, y reservaciones.

---
## Autores ✒️

* **Nilson Casco**
* **Juan Ovelar**
* **Thamara Villalba**

---
## Estructura del Proyecto 📂

El proyecto sigue una arquitectura organizada y modular para facilitar su mantenimiento y escalabilidad.
---
## Instalación y Ejecución ⚙️

Sigue estos pasos para levantar el servidor en tu entorno local.

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/N1lzon/parking-backend.git](https://github.com/N1lzon/parking-backend.git)
    cd parking-backend
    ```

2.  **Instalar dependencias:**
    ```bash
    npm install
    ```

3.  **Configurar variables de entorno:**
    Crea un archivo `.env` en la raíz del proyecto, basándote en `.env.example`, y define las variables necesarias como la URI de tu base de datos MongoDB y el secreto para JWT.
    ```env
    MONGODB_URI=mongodb://localhost/parkingdb
    SECRET=your-secret-key
    ```

4.  **Ejecutar el servidor:**
    ```bash
    npm run dev
    ```
    El servidor se iniciará en modo de desarrollo usando `nodemon`, generalmente en el puerto `3000`.

---
## Dependencias Principales 📦

* **Express**: Framework web para Node.js.
* **Mongoose**: ODM para modelar datos de MongoDB.
* **JSON Web Token (jsonwebtoken)**: Para la generación y verificación de tokens de autenticación.
* **Bcrypt.js**: Para el hasheo y la comparación de contraseñas.
* **Dotenv**: Para cargar variables de entorno desde un archivo `.env`.
* **Cors**: Para habilitar el Cross-Origin Resource Sharing.
* **Helmet**: Ayuda a securizar las aplicaciones de Express estableciendo varias cabeceras HTTP.
* **Morgan**: Logger de peticiones HTTP.

---
## Documentación de la API 📖

La API está protegida y la mayoría de los endpoints requieren un token de autenticación (`x-access-token`) en la cabecera.

### Autenticación (`/api/auth`)

#### `POST /api/auth/signup`
Registra un nuevo usuario en el sistema.

* **Body:**
    ```json
    {
      "username": "nuevo_usuario",
      "email": "usuario@correo.com",
      "password": "unaClaveSegura123",
      "roles": ["user"]
    }
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

#### `POST /api/auth/signin`
Inicia sesión y obtiene un token de autenticación.

* **Body:**
    ```json
    {
      "email": "usuario@correo.com",
      "password": "unaClaveSegura123"
    }
    ```
* **Respuesta Exitosa (200 OK):**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
    }
    ```

---
### Usuarios (`/api/users`)

*Se requiere token de administrador.*

#### `GET /api/users`
Obtiene una lista de todos los usuarios.

#### `GET /api/users/:id`
Obtiene un usuario específico por su ID.

#### `PUT /api/users/:id`
Actualiza la información de un usuario.

#### `DELETE /api/users/:id`
Elimina un usuario del sistema.

---
### Estacionamiento (`/api/parking`)

*Se requiere token de autenticación.*

#### `POST /api/parking`
Crea un nuevo lugar de estacionamiento. Se requiere rol de administrador.

* **Body:**
    ```json
    {
      "spot_number": 101,
      "location": "Piso 1, Sección A",
      "is_available": true
    }
    ```
* **Respuesta Exitosa (201 Created):**
    ```json
    {
      "is_available": true,
      "_id": "60d0fe4f5b3a0b3e4c8f3b2a",
      "spot_number": 101,
      "location": "Piso 1, Sección A",
      "createdAt": "2025-10-28T23:58:39.988Z",
      "updatedAt": "2025-10-28T23:58:39.988Z"
    }
    ```

#### `GET /api/parking`
Obtiene la lista de todos los lugares de estacionamiento.

#### `GET /api/parking/:id`
Obtiene un lugar de estacionamiento por su ID.

#### `PUT /api/parking/:id`
Actualiza un lugar de estacionamiento. Se requiere rol de administrador.

#### `DELETE /api/parking/:id`
Elimina un lugar de estacionamiento. Se requiere rol de administrador.

---
### Reservaciones (`/api/reservations`)

*Se requiere token de autenticación.*

#### `POST /api/reservations`
Crea una nueva reservación. El `user` y `parking_spot` son IDs de MongoDB.

* **Body:**
    ```json
    {
      "user": "60d0fe4f5b3a0b3e4c8f3b2b",
      "parking_spot": "60d0fe4f5b3a0b3e4c8f3b2a",
      "start_time": "2025-11-01T10:00:00.000Z",
      "end_time": "2025-11-01T12:00:00.000Z"
    }
    ```
* **Respuesta Exitosa (201 Created):**
    ```json
    {
      "status": "confirmed",
      "_id": "60d100b45b3a0b3e4c8f3b2d",
      "user": "60d0fe4f5b3a0b3e4c8f3b2b",
      "parking_spot": "60d0fe4f5b3a0b3e4c8f3b2a",
      "start_time": "2025-11-01T10:00:00.000Z",
      "end_time": "2025-11-01T12:00:00.000Z",
      "createdAt": "2025-10-28T23:59:00.000Z",
      "updatedAt": "2025-10-28T23:59:00.000Z"
    }
    ```

#### `GET /api/reservations`
Obtiene todas las reservaciones (solo administradores).

#### `GET /api/reservations/user/:userId`
Obtiene todas las reservaciones de un usuario específico.

#### `GET /api/reservations/:id`
Obtiene una reservación por su ID.

#### `PUT /api/reservations/:id`
Actualiza una reservación (ej. para cambiar el estado o la hora).

#### `DELETE /api/reservations/:id`
Cancela o elimina una reservación.
from app.database import engine, SessionLocal, Base
from app import models, crud, schemas

def init_database():
    """Inicializar la base de datos con datos de prueba"""
    
    print("Recreando tablas...")
    # ⚠️ Esto elimina todas las tablas existentes
    Base.metadata.drop_all(bind=engine)
    # Y las vuelve a crear con la definición actual de models.py
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        print("Creando 20 espacios de estacionamiento...")
        # Crear 30 espacios - primeros 5 reservados, resto no reservados
        for i in range(1, 31):
            espacio = schemas.EspacioCreate(
                numero_de_espacio=i,
                estado="libre",
                reservado="si" if i <= 5 else "no"
            )
            crud.create_espacio(db=db, espacio=espacio)
        
        print("✓ 30 espacios creados exitosamente")
        print("  - Espacios 1-5: RESERVADOS")
        print("  - Espacios 6-30: NO RESERVADOS")
        
        # Crear administradores
        print("\nCreando administradores...")
        admins_ejemplo = [
            {"nombre": "admin", "contraseña": "admin123"},
            {"nombre": "supervisor", "contraseña": "super123"}
        ]
        
        for admin_data in admins_ejemplo:
            admin = schemas.AdminCreate(**admin_data)
            crud.create_admin(db=db, admin=admin)
            print(f"✓ Admin '{admin_data['nombre']}' creado")
        
        # Crear usuarios con derecho a reserva
        print("\nCreando usuarios con derecho a reserva...")
        usuarios_ejemplo = [
            {"ci": 12345678, "nombre": "Juan Pérez"},
            {"ci": 87654321, "nombre": "María Gómez"},
            {"ci": 11223344, "nombre": "Carlos López"}
        ]
        
        for usuario_data in usuarios_ejemplo:
            usuario = schemas.UsuarioReservaCreate(**usuario_data)
            crud.create_usuario_reserva(db=db, usuario=usuario)
            print(f"✓ Usuario '{usuario_data['nombre']}' (CI: {usuario_data['ci']}) creado")
        
        print("\n" + "="*70)
        print("¡Base de datos inicializada correctamente!")
        print("="*70)
        
        print("\n🔐 CREDENCIALES DE ADMINISTRADORES:")
        print("  Usuario: admin       | Contraseña: admin123")
        print("  Usuario: supervisor  | Contraseña: super123")
        
        print("\n👤 USUARIOS CON DERECHO A RESERVA:")
        print("  CI: 12345678 | Nombre: Juan Pérez")
        print("  CI: 87654321 | Nombre: María Gómez")
        print("  CI: 11223344 | Nombre: Carlos López")
        
        print("\n🅿️  ESPACIOS:")
        print("  Espacios 1-5:   RESERVADOS (solo para usuarios con reserva)")
        print("  Espacios 6-30:  NO RESERVADOS (para usuarios normales)")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()

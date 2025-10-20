from app.database import engine, SessionLocal, Base
from app import models, crud, schemas

def init_database():
    """Inicializar la base de datos con datos de prueba"""
    
    print("Creando tablas...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Verificar si ya hay datos
        espacios_existentes = db.query(models.Espacio).count()
        
        if espacios_existentes > 0:
            print("La base de datos ya tiene datos. No se inicializará nuevamente.")
            return
        
        print("Creando 20 espacios de estacionamiento...")
        # Crear 20 espacios
        for i in range(1, 21):
            espacio = schemas.EspacioCreate(
                numero_de_espacio=f"{i:02d}",  # 01, 02, 03, ..., 20
                estado="libre"
            )
            crud.create_espacio(db=db, espacio=espacio)
        
        print("✓ 20 espacios creados exitosamente")
        
        # Crear algunos usuarios de ejemplo
        print("\nCreando usuarios de ejemplo...")
        usuarios_ejemplo = [
            {"nombre": "admin", "contraseña": "admin123"},
            {"nombre": "juan.perez", "contraseña": "1234"},
            {"nombre": "maria.gomez", "contraseña": "5678"}
        ]
        
        for user_data in usuarios_ejemplo:
            usuario = schemas.UsuarioCreate(**user_data)
            crud.create_usuario(db=db, usuario=usuario)
            print(f"✓ Usuario '{user_data['nombre']}' creado")
        
        print("\n¡Base de datos inicializada correctamente!")
        print("\nCredenciales de prueba:")
        print("  Usuario: admin | Contraseña: admin123")
        print("  Usuario: juan.perez | Contraseña: 1234")
        print("  Usuario: maria.gomez | Contraseña: 5678")
        
    except Exception as e:
        print(f"Error al inicializar la base de datos: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_database()
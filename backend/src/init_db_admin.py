"""
Script para crear usuario administrador inicial en la base de datos.
Ejecutar despues de inicializar la base de datos.
"""
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio actual al path para importar modulos
sys.path.insert(0, str(Path(__file__).parent))

from core.database import SessionLocal, init_db
from core.security import hash_password
from core.config import settings

# Importar todos los modelos para registrarlos
from models import usuario, perfil_cargo, cv, analisis, portal_credential, upload_batch, analysis_batch, session

from models.usuario import Usuario


def crear_usuario_admin():
    """Crea un usuario administrador inicial si no existe."""

    # Inicializar base de datos (crear tablas)
    print("[*] Inicializando base de datos...")
    init_db()
    print("[+] Base de datos inicializada correctamente")

    # Crear sesion
    db = SessionLocal()

    try:
        # Datos del admin
        email_admin = "admin@test.com"
        nombre_admin = "Admin"
        password_admin = "admin123"

        # Verificar si el usuario ya existe
        usuario_existente = db.query(Usuario).filter(
            Usuario.email == email_admin
        ).first()

        if usuario_existente:
            print(f"[!] El usuario '{email_admin}' ya existe en la base de datos")
            print(f"    ID: {usuario_existente.id}")
            print(f"    Nombre: {usuario_existente.nombre}")
            print(f"    Rol: {usuario_existente.rol}")
            return False

        # Hashear la contraseña
        password_hash = hash_password(password_admin)

        # Crear nuevo usuario admin
        nuevo_admin = Usuario(
            email=email_admin,
            nombre=nombre_admin,
            password_hash=password_hash,
            rol="admin",
            created_at=datetime.utcnow()
        )

        # Guardar en base de datos
        db.add(nuevo_admin)
        db.commit()
        db.refresh(nuevo_admin)

        print("[+] Usuario administrador creado exitosamente!")
        print(f"    ID: {nuevo_admin.id}")
        print(f"    Email: {nuevo_admin.email}")
        print(f"    Nombre: {nuevo_admin.nombre}")
        print(f"    Rol: {nuevo_admin.rol}")
        print(f"    Creado: {nuevo_admin.created_at}")
        print("\n[CREDENCIALES]")
        print(f"    Email: {email_admin}")
        print(f"    Password: {password_admin}")
        print("\n[!] IMPORTANTE! Cambia la contraseña despues del primer login")

        return True

    except Exception as e:
        print(f"[-] Error al crear usuario admin: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    print(f"[*] Iniciando creacion de usuario administrador...")
    print(f"    Database: {settings.database_url}")
    print()

    exito = crear_usuario_admin()

    if exito:
        print("\n[OK] Listo para usar la aplicacion!")
        sys.exit(0)
    else:
        sys.exit(1)

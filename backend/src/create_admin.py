"""
Script para crear un usuario administrador en la base de datos.
Uso: python create_admin.py
"""
import sys
from datetime import datetime
from passlib.context import CryptContext
from core.database import init_db, SessionLocal
from models.usuario import Usuario

def crear_admin():
    """Crea un usuario administrador."""
    init_db()

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    email = "tu@email.com"
    contraseña = "tu_password"
    contraseña_hasheada = pwd_context.hash(contraseña)

    db = SessionLocal()

    try:
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            print(f"✗ El usuario {email} ya existe")
            return False

        usuario = Usuario(
            email=email,
            nombre="Administrador",
            password=contraseña_hasheada,
            rol="administrador",
            created_at=datetime.utcnow()
        )
        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        print("✓ Usuario administrador creado exitosamente")
        print(f"  Email: {email}")
        print(f"  Contraseña: {contraseña}")
        print(f"  Rol: administrador")
        print(f"  ID: {usuario.id}")
        return True

    except Exception as e:
        print(f"✗ Error al crear usuario: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    crear_admin()

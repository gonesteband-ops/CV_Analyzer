"""
Script para inicializar la base de datos y crear usuario admin.
"""
import sys
from pathlib import Path
import os

# Agregar backend/src al path
sys.path.insert(0, str(Path(__file__).parent))

from core.database import init_db, SessionLocal
from core.config import settings
from models.usuario import Usuario
from models.session import Session as SessionModel
from core.security import hash_password

def main():
    # Imprimir ruta absoluta de la base de datos
    db_url = settings.database_url
    if db_url.startswith('sqlite:///'):
        db_path = db_url.replace('sqlite:///', '')
        if not Path(db_path).is_absolute():
            # Ruta relativa se resuelve desde el directorio de trabajo actual
            abs_path = Path.cwd() / db_path
        else:
            abs_path = Path(db_path)
    else:
        abs_path = Path(db_url)
    
    print(f"=" * 60)
    print(f"DATABASE_URL: {db_url}")
    print(f"Ruta absoluta DB: {abs_path.resolve()}")
    print(f"CWD actual: {Path.cwd()}")
    print(f"DB existe: {abs_path.resolve().exists()}")
    print(f"=" * 60)
    
    print("Inicializando base de datos...")
    init_db()
    print("Base de datos inicializada.")
    
    db = SessionLocal()
    
    # Verificar si ya existe admin y eliminarlo para recrear con nuevo hash
    admin = db.query(Usuario).filter(Usuario.email == "admin@empresa.cl").first()
    if admin:
        print(f"Eliminando usuario admin existente: {admin.email}")
        # Primero eliminar sesiones asociadas (cascade no funciona en SQLite directo)
        db.query(SessionModel).filter(SessionModel.user_id == admin.id).delete()
        db.commit()
        # Ahora eliminar el usuario
        db.delete(admin)
        db.commit()
        print("Usuario y sesiones eliminados.")
    
    print("Creando usuario admin...")
    admin = Usuario(
        email="admin@empresa.cl",
        password_hash=hash_password("Admin1234"),
        nombre="Administrador",
        rol="administrador"
    )
    db.add(admin)
    db.commit()
    print(f"Usuario creado: {admin.email} / Admin1234")
    
    # Verificar que se guardó correctamente
    db_admin = db.query(Usuario).filter(Usuario.email == "admin@empresa.cl").first()
    print(f"Usuario en DB: {db_admin.email}, hash: {db_admin.password_hash[:20]}...")
    
    db.close()
    print("¡Listo!")

if __name__ == "__main__":
    main()

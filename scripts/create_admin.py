"""
Script para crear el primer usuario administrador.
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from sqlalchemy.orm import Session
from core.database import SessionLocal, init_db
from models.usuario import Usuario
from core.security import hash_password, verificar_password_fortaleza
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def crear_admin() -> None:
    """
    Crea el primer usuario administrador del sistema.
    """
    logger.info("Creando usuario administrador...")
    
    # Inicializar base de datos si no existe
    init_db()
    
    db = SessionLocal()
    
    try:
        # Verificar si ya existe un admin
        admin_existente = db.query(Usuario).filter(
            Usuario.rol == "admin"
        ).first()
        
        if admin_existente:
            logger.warning(f"Ya existe un administrador: {admin_existente.email}")
            return
        
        # Solicitar datos al usuario
        print("\n=== Crear Usuario Administrador ===\n")
        
        email = input("Email: ").strip()
        if not email:
            logger.error("El email es requerido")
            return
        
        # Validar formato de email
        if "@" not in email or "." not in email:
            logger.error("Email inválido")
            return
        
        # Verificar si ya existe
        usuario_existente = db.query(Usuario).filter(Usuario.email == email).first()
        if usuario_existente:
            logger.error(f"El email {email} ya está registrado")
            return
        
        nombre = input("Nombre completo: ").strip()
        if not nombre:
            logger.error("El nombre es requerido")
            return
        
        # Input de contraseña con validación
        while True:
            password = input("Contraseña: ").strip()
            es_valida, error = verificar_password_fortaleza(password)
            
            if not es_valida:
                logger.error(f"Contraseña débil: {error}")
                continue
            
            password_confirm = input("Confirmar contraseña: ").strip()
            
            if password != password_confirm:
                logger.error("Las contraseñas no coinciden")
                continue
            
            break
        
        # Crear usuario
        usuario = Usuario(
            email=email,
            password_hash=hash_password(password),
            nombre=nombre,
            rol="admin"
        )
        
        db.add(usuario)
        db.commit()
        db.refresh(usuario)
        
        logger.info(f"✅ Administrador creado exitosamente: {usuario.email}")
        logger.info(f"   ID: {usuario.id}")
        logger.info(f"   Nombre: {usuario.nombre}")
        logger.info(f"   Rol: {usuario.rol}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"❌ Error al crear administrador: {e}")
        raise
    finally:
        db.close()


def main() -> None:
    """
    Función principal del script.
    """
    try:
        crear_admin()
    except KeyboardInterrupt:
        print("\n\nOperación cancelada por el usuario")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

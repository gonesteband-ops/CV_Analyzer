"""
Script de migración de base de datos.
"""
import sys
from pathlib import Path

# Agregar el directorio src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.database import engine, Base
from core.config import settings
import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def upgrade() -> None:
    """
    Aplica todas las migraciones pendientes (crea las tablas).
    """
    logger.info("Iniciando migración de base de datos...")
    logger.info(f"Database URL: {settings.database_url}")
    
    try:
        # Importar todos los modelos para que se registren en Base
        from models import usuario, perfil_cargo, cv, analisis, portal_credential
        
        # Crear todas las tablas
        Base.metadata.create_all(bind=engine)
        
        logger.info("✅ Migración completada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error en migración: {e}")
        raise


def downgrade() -> None:
    """
    Elimina todas las tablas de la base de datos.
    ADVERTENCIA: Esto elimina todos los datos.
    """
    logger.warning("⚠️  ¡ADVERTENCIA! Esto eliminará todas las tablas y datos.")
    confirm = input("¿Está seguro que desea continuar? (yes/no): ")
    
    if confirm.lower() != "yes":
        logger.info("Operación cancelada")
        return
    
    try:
        # Importar todos los modelos
        from models import usuario, perfil_cargo, cv, analisis, portal_credential
        
        # Eliminar todas las tablas
        Base.metadata.drop_all(bind=engine)
        
        logger.info("✅ Base de datos eliminada exitosamente")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


def current() -> None:
    """
    Muestra el estado actual de la base de datos.
    """
    from sqlalchemy import inspect
    
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if not tables:
            logger.info("La base de datos está vacía (sin tablas)")
        else:
            logger.info(f"Tablas existentes ({len(tables)}):")
            for table in tables:
                logger.info(f"  - {table}")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        raise


def main() -> None:
    """
    Función principal del script de migración.
    """
    if len(sys.argv) < 2:
        print("Uso: python migrate.py <comando>")
        print("\nComandos disponibles:")
        print("  upgrade   - Aplica migraciones (crea tablas)")
        print("  downgrade - Elimina todas las tablas")
        print("  current   - Muestra estado actual")
        sys.exit(1)
    
    comando = sys.argv[1].lower()
    
    if comando == "upgrade":
        upgrade()
    elif comando == "downgrade":
        downgrade()
    elif comando == "current":
        current()
    else:
        logger.error(f"Comando desconocido: {comando}")
        sys.exit(1)


if __name__ == "__main__":
    main()

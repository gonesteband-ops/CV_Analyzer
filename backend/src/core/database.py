"""
Configuración de base de datos SQLAlchemy.
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings

# Ruta de la base de datos SQLite.
# Por defecto backend/src/analizer.db; se puede sobreescribir con DB_PATH
# (útil en Docker o despliegues con volumen persistente).
DB_PATH = Path(os.getenv("DB_PATH") or Path(__file__).parent.parent / "analizer.db")


def create_database_engine() -> create_engine:
    """
    Crea el engine de base de datos según la URL configurada.

    Returns:
        Engine: Engine de SQLAlchemy configurado.
    """
    # Construir URL con ruta absoluta para SQLite
    db_url = settings.database_url
    
    if db_url.startswith("sqlite"):
        # Usar ruta absoluta para evitar problemas de directorio de trabajo
        db_path = DB_PATH.as_posix()
        db_url = f"sqlite:///{db_path}"
        
        # SQLite requiere argumentos especiales para async
        return create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug,
        )
    elif db_url.startswith("postgresql"):
        # PostgreSQL para producción
        return create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.debug,
        )
    else:
        raise ValueError(f"Database URL no soportada: {db_url}")


# Engine global
engine = create_database_engine()

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base para modelos
Base = declarative_base()


def get_db() -> SessionLocal:
    """
    Dependencia de FastAPI para obtener sesión de base de datos.
    
    Yields:
        Session: Sesión de SQLAlchemy.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Inicializa la base de datos creando todas las tablas.
    """
    # Importar todos los modelos para que se registren en Base
    from models import usuario, perfil_cargo, cv, analisis, portal_credential, upload_batch, analysis_batch, session

    Base.metadata.create_all(bind=engine)

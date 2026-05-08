"""
Configuración de base de datos SQLAlchemy.
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core.config import settings


def create_database_engine() -> create_engine:
    """
    Crea el engine de base de datos según la URL configurada.
    
    Returns:
        Engine: Engine de SQLAlchemy configurado.
    """
    if settings.database_url.startswith("sqlite"):
        # SQLite requiere argumentos especiales para async
        return create_engine(
            settings.database_url,
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=settings.debug,
        )
    elif settings.database_url.startswith("postgresql"):
        # PostgreSQL para producción
        return create_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=settings.debug,
        )
    else:
        raise ValueError(f"Database URL no soportada: {settings.database_url}")


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

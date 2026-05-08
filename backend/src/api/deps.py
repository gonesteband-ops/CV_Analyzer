"""
Dependencias de FastAPI para inyección de dependencias.
Provee get_db, get_current_user y otras dependencias compartidas.
"""
import logging
from typing import Generator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from core.database import SessionLocal
from models.usuario import Usuario

logger = logging.getLogger(__name__)


def get_db() -> Generator[Session, None, None]:
    """
    Dependencia que provee sesión de base de datos.
    
    Yields:
        Session: Sesión de SQLAlchemy.
        
    Example:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(request: Request) -> Usuario | None:
    """
    Dependencia que obtiene el usuario actual del request state.
    
    El usuario es inyectado por AuthMiddleware durante el procesamiento del request.
    
    Args:
        request: Request de FastAPI.
        
    Returns:
        Usuario actual o None si no está autenticado.
    """
    return getattr(request.state, "usuario", None)


def require_auth(usuario: Usuario | None = Depends(get_current_user)) -> Usuario:
    """
    Dependencia que requiere autenticación.
    
    Lanza HTTPException 401 si el usuario no está autenticado.
    
    Args:
        usuario: Usuario actual (inyectado por get_current_user).
        
    Returns:
        Usuario autenticado.
        
    Raises:
        HTTPException: Si no está autenticado (401 Unauthorized).
    """
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No autenticado. Inicie sesión para continuar.",
            headers={"HX-Redirect": "/login"},  # Para HTMX
        )
    return usuario


def require_admin(usuario: Usuario = Depends(require_auth)) -> Usuario:
    """
    Dependencia que requiere rol de administrador.

    Args:
        usuario: Usuario autenticado.

    Returns:
        Usuario administrador.

    Raises:
        HTTPException: Si no es admin (403 Forbidden).
    """
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado. Se requiere rol de administrador.",
        )
    return usuario


# Dependencias compuestas (convenience)
def get_db_and_user(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
) -> tuple[Session, Usuario]:
    """
    Dependencia compuesta que provee DB y usuario autenticado.
    
    Returns:
        Tuple[Session, Usuario]: Sesión y usuario.
    """
    return db, usuario

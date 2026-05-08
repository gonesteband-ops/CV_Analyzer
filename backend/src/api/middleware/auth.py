"""
Middleware de autenticación para FastAPI.
Verifica que las rutas protegidas requieran sesión válida.
"""
import logging
from datetime import datetime
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse

from core.database import SessionLocal
from models.usuario import Usuario
from models.session import Session

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica autenticación en rutas protegidas.

    Funcionamiento:
    1. Extrae session_id de las cookies
    2. Valida que la sesión exista y sea válida
    3. Agrega usuario actual al request state
    4. Redirige a /login si no está autenticado en rutas protegidas
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Procesa cada request verificando autenticación.

        Args:
            request: Request de FastAPI.
            call_next: Siguiente middleware/handler.

        Returns:
            Response procesado.
        """
        # Rutas públicas (no requieren autenticación)
        rutas_publicas = [
            "/login",
            "/api/auth/login",
            "/api/auth/recover",
            "/api/auth/reset",
            "/api/candidates/upload",
            "/recuperar-password",
            "/static",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
        ]

        # Verificar si la ruta es pública
        path = request.url.path
        es_ruta_publica = any(
            path.startswith(ruta) for ruta in rutas_publicas
        )

        # Obtener session_id de cookies
        session_id = request.cookies.get("session_id")

        # Intentar obtener usuario de la sesión
        usuario_actual = None

        if session_id:
            try:
                db = SessionLocal()
                # Buscar sesión válida
                sesion = db.query(Session).filter(
                    Session.session_id == session_id,
                    Session.is_active == True,
                ).first()

                if sesion and sesion.es_valida():
                    # Obtener usuario asociado
                    usuario_actual = db.query(Usuario).filter(
                        Usuario.id == sesion.user_id
                    ).first()
                    logger.debug(f"Sesión válida para usuario {usuario_actual.email if usuario_actual else 'N/A'}")

                db.close()
            except Exception as e:
                logger.error(f"Error al validar sesión: {e}")

        # Agregar usuario al request state
        request.state.usuario = usuario_actual
        request.state.es_autenticado = usuario_actual is not None
        
        # Si no es autenticado y la ruta es protegida, redirigir a login
        if not es_ruta_publica and not request.state.es_autenticado:
            # Para requests HTMX, retornar header de redirección
            if request.headers.get("HX-Request") == "true":
                response = await call_next(request)
                response.headers["HX-Redirect"] = "/login"
                return response
            
            # Para requests normales, redirigir
            return RedirectResponse(url="/login")
        
        # Procesar request normalmente
        response = await call_next(request)
        return response


def actualizar_ultimo_acceso(usuario_id: int) -> None:
    """
    Actualiza el timestamp de último acceso del usuario.
    
    Args:
        usuario_id: ID del usuario.
    """
    try:
        db = SessionLocal()
        usuario = db.query(Usuario).filter(Usuario.id == usuario_id).first()
        if usuario:
            usuario.last_login = datetime.utcnow()
            db.commit()
        db.close()
    except Exception as e:
        logger.error(f"Error al actualizar último acceso: {e}")

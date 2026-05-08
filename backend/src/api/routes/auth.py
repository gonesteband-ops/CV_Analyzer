"""
Rutas de API para autenticación.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from api.deps import get_db, get_current_user
from core.config import settings
from core.database import SessionLocal
from core.security import verificar_password
from models.usuario import Usuario
from models.session import Session as SessionModel
from services.password_reset_service import PasswordResetService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Autenticación"])


class LoginRequest(BaseModel):
    """Schema para request de login."""

    email: str = Field(..., min_length=5, max_length=255)
    password: str = Field(..., min_length=6)

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Normaliza el email a minúsculas."""
        return v.strip().lower()


class LoginResponse(BaseModel):
    """Schema para respuesta de login."""

    success: bool
    message: str
    redirect: Optional[str] = None
    user: Optional[dict] = None


@router.post("/login")
async def login(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Autentica un usuario con email y contraseña.

    Args:
        request: Request de FastAPI.
        db: Sesión de base de datos.

    Returns:
        RedirectResponse a la página de inicio.
    """
    # Leer datos del form (HTMX envía application/x-www-form-urlencoded)
    form_data = await request.form()
    email = form_data.get("email", "")
    password = form_data.get("password", "")

    # Normalizar email
    email = str(email).strip().lower()

    logger.info(f"Intento de login con email: {email}, password: {password}")

    # Buscar usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == email).first()

    logger.info(f"Usuario encontrado: {usuario is not None}")

    # Verificar credenciales
    if usuario:
        logger.info(f"Hash almacenado: {usuario.password_hash}")
        es_valida = verificar_password(str(password), usuario.password_hash)
        logger.info(f"Contrasena valida: {es_valida}")

    if not usuario or not verificar_password(str(password), usuario.password_hash):
        logger.warning(f"Intento de login fallido para email: {email}")
        # Redirigir a login con parámetro de error
        return RedirectResponse(url="/login?error=invalid_credentials", status_code=303)

    # Generar session_id único y guardar en DB
    try:
        # Crear sesión en base de datos
        nueva_sesion = SessionModel.crear_session(user_id=usuario.id, duracion_dias=7)
        db.add(nueva_sesion)

        # Actualizar last_login del usuario
        usuario.last_login = datetime.utcnow()
        db.commit()

        session_id = nueva_sesion.session_id
        logger.info(f"Usuario {usuario.email} (id={usuario.id}) inició sesión con session_id={session_id[:8]}...")
    except Exception as e:
        logger.error(f"Error al guardar sesión: {e}")
        db.rollback()
        return RedirectResponse(url="/login?error=server_error", status_code=303)

    # Crear respuesta de redirección con cookie
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=86400 * 7,  # 7 días
        path="/",
        httponly=settings.session_cookie_httponly,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )

    return response


@router.post("/logout")
async def logout(
    request: Request,
    usuario: Usuario = Depends(get_current_user),
):
    """
    Cierra la sesión del usuario actual.

    Args:
        request: Request de FastAPI.
        usuario: Usuario autenticado.

    Returns:
        RedirectResponse a /login.
    """
    response = RedirectResponse(url="/login")
    response.delete_cookie(
        key="session_id",
        path="/",
    )
    logger.info(f"Usuario {usuario.email} cerró sesión")
    return response


@router.post("/recover")
async def recover_password(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Solicita recuperación de contraseña.

    TODO: Implementar envío de email con token de recuperación.
    """
    # Por ahora retornamos éxito sin hacer nada
    return JSONResponse(
        content={
            "success": True,
            "message": "Si el email existe, se enviarán instrucciones de recuperación",
        }
    )


class ResetPasswordRequest(BaseModel):
    """Schema para request de reseteo de password."""
    token: str = Field(..., description="Token de reseteo")
    nuevo_password: str = Field(..., min_length=8, description="Nueva contraseña (mínimo 8 caracteres)")


@router.post("/reset-password")
async def generar_token_reseteo(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Genera un token de reseteo para un usuario por su email.
    """
    try:
        # Parsear body manualmente
        body = await request.json()
        email = body.get("email", "").strip().lower()
        expires_hours = body.get("expires_hours", 24)
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email es requerido"
            )
        
        service = PasswordResetService(db)
        token = service.generar_token_reseteo(email, expires_hours)
        
        if not token:
            # No revelar si el usuario existe o no
            return JSONResponse(
                content={
                    "success": True,
                    "message": "Si el email existe, se enviarán instrucciones de recuperación",
                }
            )
        
        # En producción, aquí se enviaría el email con el token
        # Por ahora, retornamos el token en la respuesta (solo para desarrollo)
        return JSONResponse(
            content={
                "success": True,
                "message": "Token generado exitosamente",
                "token": token,  # Solo para desarrollo, eliminar en producción
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al generar token de reseteo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el token"
        )


@router.post("/confirm-reset")
async def confirmar_reseteo(
    data: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Confirma el reseteo de contraseña con un token válido.
    """
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        service = PasswordResetService(db)
        
        # Hashear nueva password
        password_hash = pwd_context.hash(data.nuevo_password)
        
        # Resetear password
        exito, mensaje = service.resetear_password(
            token=data.token,
            nuevo_password_hash=password_hash
        )
        
        if not exito:
            raise HTTPException(status_code=400, detail=mensaje)
        
        return JSONResponse(
            content={
                "success": True,
                "message": mensaje,
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al confirmar reseteo: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al confirmar el reseteo"
        )


@router.post("/reset")
async def reset_password(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Resetea la contraseña con un token.

    TODO: Implementar reset con token válido.
    """
    # Por ahora retornamos éxito sin hacer nada
    return JSONResponse(
        content={
            "success": True,
            "message": "Contraseña reseteada exitosamente",
        }
    )

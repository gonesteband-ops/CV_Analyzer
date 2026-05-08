"""
Servicio de reseteo de password.
"""
import logging
import secrets
from datetime import datetime
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from models.usuario import Usuario

logger = logging.getLogger(__name__)


class PasswordResetService:
    """
    Servicio para gestión de reseteo de password con tokens.
    """

    def __init__(self, db: Session):
        """
        Inicializa el servicio con la sesión de base de datos.
        
        Args:
            db: Sesión de base de datos
        """
        self.db = db

    def generar_token_reseteo(self, email: str, expires_hours: int = 24) -> Optional[str]:
        """
        Genera un token de reseteo para un usuario por su email.
        
        Args:
            email: Email del usuario
            expires_hours: Horas de validez del token (por defecto 24)
            
        Returns:
            Token generado si el usuario existe, None en caso contrario
        """
        usuario = self.db.query(Usuario).filter(Usuario.email == email).first()
        
        if not usuario:
            logger.warning(f"No se encontró usuario con email: {email}")
            return None
        
        # Generar token único
        token = secrets.token_urlsafe(32)
        
        # Establecer token en el usuario
        usuario.set_reset_token(token, expires_hours)
        self.db.commit()
        
        logger.info(f"Token de reseteo generado para usuario: {email}")
        return token

    def validar_token(self, token: str) -> Tuple[bool, Optional[Usuario]]:
        """
        Valida un token de reseteo.
        
        Args:
            token: Token a validar
            
        Returns:
            Tupla (es_valido, usuario):
                - es_valido: True si el token es válido
                - usuario: Objeto Usuario si es válido, None en caso contrario
        """
        if not token:
            return False, None
        
        usuario = self.db.query(Usuario).filter(Usuario.reset_token == token).first()
        
        if not usuario:
            logger.warning(f"Token no encontrado: {token[:8]}...")
            return False, None
        
        if not usuario.is_reset_token_valid():
            logger.warning(f"Token expirado para usuario: {usuario.email}")
            return False, usuario
        
        return True, usuario

    def resetear_password(
        self,
        token: str,
        nuevo_password_hash: str
    ) -> Tuple[bool, str]:
        """
        Resetea la password de un usuario usando un token válido.
        
        Args:
            token: Token de reseteo
            nuevo_password_hash: Hash de la nueva password
            
        Returns:
            Tupla (exitoso, mensaje):
                - exitoso: True si se reseteó exitosamente
                - mensaje: Mensaje descriptivo del resultado
        """
        es_valido, usuario = self.validar_token(token)
        
        if not es_valido:
            if not usuario:
                return False, "Token inválido o no encontrado"
            return False, "Token expirado. Por favor solicite uno nuevo"
        
        # Actualizar password
        usuario.password_hash = nuevo_password_hash
        
        # Invalidar token
        usuario.clear_reset_token()
        
        self.db.commit()
        
        logger.info(f"Password reseteada exitosamente para usuario: {usuario.email}")
        return True, "Password actualizada exitosamente"

    def invalidar_token(self, email: str) -> bool:
        """
        Invalida cualquier token de reseteo activo para un usuario.
        
        Args:
            email: Email del usuario
            
        Returns:
            True si se invalidó el token, False si no existe el usuario
        """
        usuario = self.db.query(Usuario).filter(Usuario.email == email).first()
        
        if not usuario:
            return False
        
        if usuario.reset_token:
            usuario.clear_reset_token()
            self.db.commit()
            logger.info(f"Token de reseteo invalidado para usuario: {email}")
        
        return True

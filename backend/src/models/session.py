"""
Modelo de Sesión de Usuario.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from core.database import Base


class Session(Base):
    """
    Representa una sesión activa de un usuario.

    Almacena session_id para validar autenticación.
    """

    __tablename__ = "sesion"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)

    # Relación con usuario
    user = relationship("Usuario", backref="sessions")

    def __repr__(self) -> str:
        """Representación en string de la sesión."""
        return f"<Session(id={self.id}, session_id='{self.session_id[:8]}...', user_id={self.user_id})>"

    @classmethod
    def crear_session(cls, user_id: int, duracion_dias: int = 7) -> "Session":
        """
        Crea una nueva sesión con fecha de expiración.

        Args:
            user_id: ID del usuario.
            duracion_dias: Duración de la sesión en días.

        Returns:
            Session: Nueva sesión creada.
        """
        import uuid
        ahora = datetime.utcnow()
        return cls(
            session_id=str(uuid.uuid4()),
            user_id=user_id,
            created_at=ahora,
            expires_at=ahora + timedelta(days=duracion_dias),
            is_active=True,
        )

    def es_valida(self) -> bool:
        """
        Verifica si la sesión es válida.

        Returns:
            bool: True si es válida, False si está expirada o inactiva.
        """
        if not self.is_active:
            return False
        if self.expires_at < datetime.utcnow():
            return False
        return True

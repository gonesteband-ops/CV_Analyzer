"""
Modelo de Usuario.
"""
from datetime import datetime, timedelta
from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import relationship

from core.database import Base


class Usuario(Base):
    """
    Representa un usuario del sistema (reclutador o administrador).
    """

    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="reclutador")
    activo = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Campos para reseteo de password
    reset_token = Column(String(255), unique=True, nullable=True, index=True)
    reset_token_expires_at = Column(DateTime, nullable=True)

    # Relaciones
    perfiles = relationship(
        "PerfilCargo",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    cvs = relationship(
        "CV",
        back_populates="uploader",
        cascade="all, delete-orphan"
    )
    analisis = relationship(
        "Analisis",
        back_populates="analyst"
    )
    upload_batches = relationship(
        "UploadBatch",
        back_populates="creator",
        cascade="all, delete-orphan"
    )
    analysis_batches = relationship(
        "AnalysisBatch",
        back_populates="creator",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Representación en string del usuario."""
        return f"<Usuario(id={self.id}, email='{self.email}', nombre='{self.nombre}')>"
    
    def is_reset_token_valid(self) -> bool:
        """
        Verifica si el token de reseteo es válido (existe y no ha expirado).
        
        Returns:
            bool: True si el token es válido, False en caso contrario
        """
        if not self.reset_token or not self.reset_token_expires_at:
            return False
        return datetime.utcnow() < self.reset_token_expires_at
    
    def clear_reset_token(self):
        """Invalida el token de reseteo."""
        self.reset_token = None
        self.reset_token_expires_at = None
    
    def set_reset_token(self, token: str, expires_hours: int = 24):
        """
        Establece un token de reseteo con fecha de expiración.
        
        Args:
            token: Token de reseteo único
            expires_hours: Horas de validez del token (por defecto 24)
        """
        self.reset_token = token
        self.reset_token_expires_at = datetime.utcnow() + timedelta(hours=expires_hours)

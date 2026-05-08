"""
Modelo de Credencial de Portal.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship

from core.database import Base


class PortalCredential(Base):
    """
    Representa credenciales encriptadas para portales de empleo.
    """
    
    __tablename__ = "portal_credential"
    
    id = Column(Integer, primary_key=True, index=True)
    portal_name = Column(String(50), unique=True, nullable=False)
    cliente_id = Column(String(255), nullable=False)
    usuario = Column(String(255), nullable=False)
    encrypted_secret = Column(String(512), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self) -> str:
        """Representación en string de la credencial."""
        return f"<PortalCredential(portal='{self.portal_name}', usuario='{self.usuario}')>"

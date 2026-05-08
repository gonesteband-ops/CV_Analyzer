"""
Modelo de CV.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship

from core.database import Base


class CV(Base):
    """
    Representa un CV subido al sistema.
    """

    __tablename__ = "cv"

    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    upload_batch_id = Column(Integer, ForeignKey("upload_batch.id"), nullable=True, index=True)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="uploaded")
    extracted_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Campos para datos extraídos del CV
    candidate_name = Column(String(255), nullable=True)  # Nombre del candidato
    candidate_email = Column(String(255), nullable=True)  # Email del candidato
    candidate_phone = Column(String(50), nullable=True)  # Teléfono del candidato
    candidate_summary = Column(Text, nullable=True)  # Resumen del perfil

    # Relaciones
    uploader = relationship("Usuario", back_populates="cvs")
    upload_batch = relationship("UploadBatch", back_populates="cvs", foreign_keys=[upload_batch_id])
    analisis = relationship(
        "Analisis",
        back_populates="cv",
        uselist=False,
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Representación en string del CV."""
        return f"<CV(id={self.id}, file_name='{self.file_name}', status='{self.status}')>"

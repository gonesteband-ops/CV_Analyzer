"""
Modelo de UploadBatch para tracking de cargas masivas de CVs.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from core.database import Base


class UploadBatch(Base):
    """
    Representa un lote de uploads de CVs.
    Permite trackear el progreso de procesamiento de múltiples archivos.
    """

    __tablename__ = "upload_batch"

    id = Column(Integer, primary_key=True, index=True)
    upload_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    status = Column(String(50), nullable=False, default="uploaded")  # uploaded, parsing, parsed, error
    total_files = Column(Integer, nullable=False, default=0)
    processed_files = Column(Integer, nullable=False, default=0)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relaciones
    creator = relationship("Usuario", back_populates="upload_batches")
    cvs = relationship("CV", back_populates="upload_batch", cascade="all, delete-orphan")

    @property
    def progress(self) -> int:
        """Calcula el progreso de procesamiento como porcentaje."""
        if self.total_files == 0:
            return 0
        return int((self.processed_files / self.total_files) * 100)

    def __repr__(self) -> str:
        """Representación en string del upload batch."""
        return f"<UploadBatch(upload_id='{self.upload_id}', status='{self.status}', progress={self.progress}%)>"

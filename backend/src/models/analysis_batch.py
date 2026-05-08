"""
Modelo de AnalysisBatch para tracking de análisis masivos de CVs.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship

from core.database import Base


class AnalysisBatch(Base):
    """
    Representa un lote de análisis de CVs contra un perfil de cargo.
    Permite trackear el progreso del análisis masivo.
    """

    __tablename__ = "analysis_batch"

    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String(36), unique=True, nullable=False, index=True)  # UUID
    perfil_id = Column(Integer, ForeignKey("perfil_cargo.id"), nullable=False)
    status = Column(String(50), nullable=False, default="pending")  # pending, processing, completed, error
    total_cvs = Column(Integer, nullable=False, default=0)
    processed_cvs = Column(Integer, nullable=False, default=0)
    estimated_time_seconds = Column(Integer, nullable=True)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # Relaciones
    creator = relationship("Usuario", back_populates="analysis_batches")
    perfil = relationship("PerfilCargo", back_populates="analysis_batches")
    resultados = relationship(
        "Analisis",
        back_populates="analysis_batch",
        cascade="all, delete-orphan"
    )

    @property
    def progress(self) -> int:
        """Calcula el progreso de procesamiento como porcentaje."""
        if self.total_cvs == 0:
            return 0
        return int((self.processed_cvs / self.total_cvs) * 100)

    def __repr__(self) -> str:
        """Representación en string del analysis batch."""
        return f"<AnalysisBatch(batch_id='{self.batch_id}', status='{self.status}', progress={self.progress}%)>"

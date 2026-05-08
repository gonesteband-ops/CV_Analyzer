"""
Modelo de Análisis.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship

from core.database import Base


class Analisis(Base):
    """
    Representa el resultado de analizar un CV contra un perfil de cargo.
    """
    
    __tablename__ = "analisis"
    
    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cv.id"), nullable=False)
    perfil_id = Column(Integer, ForeignKey("perfil_cargo.id"), nullable=False)
    analysis_batch_id = Column(Integer, ForeignKey("analysis_batch.id"), nullable=True, index=True)
    puntaje = Column(Integer, nullable=False)
    etiqueta = Column(String(50), nullable=False)
    feedback = Column(Text, nullable=False)
    fortalezas = Column(Text, nullable=True)
    debilidades = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    analyzed_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)

    # Constraints
    __table_args__ = (
        CheckConstraint("puntaje >= 0 AND puntaje <= 100", name="check_puntaje_range"),
        UniqueConstraint('cv_id', 'perfil_id', name='uq_cv_perfil'),
    )
    
    # Relaciones
    cv = relationship("CV", back_populates="analisis")
    perfil = relationship("PerfilCargo", back_populates="analisis")
    analyst = relationship("Usuario", back_populates="analisis")
    analysis_batch = relationship("AnalysisBatch", back_populates="resultados")
    
    def __repr__(self) -> str:
        """Representación en string del análisis."""
        return f"<Analisis(id={self.id}, cv_id={self.cv_id}, puntaje={self.puntaje})>"

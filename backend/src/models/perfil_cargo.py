"""
Modelo de Perfil de Cargo.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Text, Boolean
from sqlalchemy.orm import relationship

from core.database import Base


class PerfilCargo(Base):
    """
    Representa un perfil de cargo para comparar CVs.
    """

    __tablename__ = "perfil_cargo"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    requisitos = Column(Text, nullable=True)
    responsabilidades = Column(Text, nullable=True)
    habilidades_requeridas = Column(JSON, nullable=True, default=list)
    habilidades_deseables = Column(JSON, nullable=True, default=list)
    nivel_experiencia = Column(String(50), nullable=True)  # Junior, Semi Senior, Senior
    salario_minimo = Column(Integer, nullable=True)  # En pesos chilenos
    salario_maximo = Column(Integer, nullable=True)  # En pesos chilenos
    departamento = Column(String(100), nullable=True)
    umbral_recomendado = Column(Integer, nullable=True, default=70)  # Puntaje mínimo para "Recomendado"
    umbral_reservas = Column(Integer, nullable=True, default=40)  # Puntaje mínimo para "Con reservas"
    peso_tecnico = Column(Integer, nullable=True, default=50)  # Peso para puntaje técnico (%)
    peso_experiencia = Column(Integer, nullable=True, default=30)  # Peso para experiencia (%)
    peso_soft_skills = Column(Integer, nullable=True, default=20)  # Peso para soft skills (%)
    penalizacion_sobrecalificado = Column(Integer, nullable=True, default=25)  # Puntos a restar si está sobrecalificado
    penalizacion_cambio_rubro = Column(Integer, nullable=True, default=15)  # Puntos a restar si cambia de rubro
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True, default=datetime.utcnow, onupdate=datetime.utcnow)
    activo = Column(Boolean, nullable=False, default=True)

    # Relaciones
    creator = relationship("Usuario", back_populates="perfiles")
    analisis = relationship("Analisis", back_populates="perfil")
    analysis_batches = relationship("AnalysisBatch", back_populates="perfil")

    def __repr__(self) -> str:
        """Representación en string del perfil."""
        return f"<PerfilCargo(id={self.id}, titulo='{self.titulo}')>"

"""
Esquemas Pydantic para validación de datos del perfil de cargo.
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime


class PerfilCargoBase(BaseModel):
    """
    Esquema base para perfil de cargo.
    """
    titulo: str = Field(..., min_length=1, max_length=255, description="Título del perfil de cargo")
    descripcion: str = Field(..., min_length=1, description="Descripción detallada del cargo")
    requisitos: Optional[str] = Field(None, description="Requisitos del cargo")
    responsabilidades: Optional[str] = Field(None, description="Responsabilidades del cargo")
    habilidades_requeridas: Optional[List[str]] = Field(None, description="Lista de habilidades requeridas")
    habilidades_deseables: Optional[List[str]] = Field(None, description="Lista de habilidades deseables")
    nivel_experiencia: Optional[str] = Field(None, description="Nivel de experiencia requerido (Junior, Semi Senior, Senior)")
    salario_minimo: Optional[int] = Field(None, ge=0, description="Salario mínimo en pesos chilenos")
    salario_maximo: Optional[int] = Field(None, ge=0, description="Salario máximo en pesos chilenos")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento al que pertenece el cargo")
    umbral_recomendado: Optional[int] = Field(70, ge=0, le=100, description="Puntaje mínimo para etiqueta 'Recomendado'")
    umbral_reservas: Optional[int] = Field(40, ge=0, le=100, description="Puntaje mínimo para etiqueta 'Con reservas'")
    peso_tecnico: Optional[int] = Field(50, ge=0, le=100, description="Peso para puntaje técnico (%)")
    peso_experiencia: Optional[int] = Field(30, ge=0, le=100, description="Peso para experiencia (%)")
    peso_soft_skills: Optional[int] = Field(20, ge=0, le=100, description="Peso para soft skills (%)")
    penalizacion_sobrecalificado: Optional[int] = Field(25, ge=0, le=100, description="Puntos a restar si está sobrecalificado")
    penalizacion_cambio_rubro: Optional[int] = Field(15, ge=0, le=100, description="Puntos a restar si cambia de rubro")
    activo: bool = Field(True)

    @field_validator('habilidades_requeridas', mode='before')
    @classmethod
    def parse_habilidades_requeridas(cls, v):
        """Convierte string CSV a lista de habilidades."""
        if v is None:
            return None
        if isinstance(v, str):
            habilidades = [h.strip() for h in v.split(',') if h.strip()]
            return habilidades if habilidades else None
        return v

    @field_validator('habilidades_deseables', mode='before')
    @classmethod
    def parse_habilidades_deseables(cls, v):
        """Convierte string CSV a lista de habilidades."""
        if v is None:
            return None
        if isinstance(v, str):
            habilidades = [h.strip() for h in v.split(',') if h.strip()]
            return habilidades if habilidades else None
        return v

    @field_validator('salario_maximo')
    @classmethod
    def validar_salario_maximo(cls, v, info):
        """Valida que el salario máximo no sea menor que el salario mínimo."""
        if v is not None and 'salario_minimo' in info.data and info.data['salario_minimo'] is not None:
            if v < info.data['salario_minimo']:
                raise ValueError('El salario máximo no puede ser menor que el salario mínimo')
        return v


class PerfilCargoCreate(PerfilCargoBase):
    """
    Esquema para crear un nuevo perfil de cargo.
    """
    pass


class PerfilCargoUpdate(BaseModel):
    """
    Esquema para actualizar un perfil de cargo.
    """
    titulo: Optional[str] = Field(None, min_length=1, max_length=255, description="Título del perfil de cargo")
    descripcion: Optional[str] = Field(None, min_length=1, description="Descripción detallada del cargo")
    requisitos: Optional[str] = Field(None, description="Requisitos del cargo")
    responsabilidades: Optional[str] = Field(None, description="Responsabilidades del cargo")
    habilidades_requeridas: Optional[List[str]] = Field(None, description="Lista de habilidades requeridas")
    habilidades_deseables: Optional[List[str]] = Field(None, description="Lista de habilidades deseables")
    nivel_experiencia: Optional[str] = Field(None, description="Nivel de experiencia requerido (Junior, Semi Senior, Senior)")
    salario_minimo: Optional[int] = Field(None, ge=0, description="Salario mínimo en pesos chilenos")
    salario_maximo: Optional[int] = Field(None, ge=0, description="Salario máximo en pesos chilenos")
    departamento: Optional[str] = Field(None, max_length=100, description="Departamento al que pertenece el cargo")
    umbral_recomendado: Optional[int] = Field(None, ge=0, le=100, description="Puntaje mínimo para etiqueta 'Recomendado'")
    umbral_reservas: Optional[int] = Field(None, ge=0, le=100, description="Puntaje mínimo para etiqueta 'Con reservas'")
    peso_tecnico: Optional[int] = Field(None, ge=0, le=100, description="Peso para puntaje técnico (%)")
    peso_experiencia: Optional[int] = Field(None, ge=0, le=100, description="Peso para experiencia (%)")
    peso_soft_skills: Optional[int] = Field(None, ge=0, le=100, description="Peso para soft skills (%)")
    penalizacion_sobrecalificado: Optional[int] = Field(None, ge=0, le=100, description="Puntos a restar si está sobrecalificado")
    penalizacion_cambio_rubro: Optional[int] = Field(None, ge=0, le=100, description="Puntos a restar si cambia de rubro")
    activo: Optional[bool] = Field(None)

    @field_validator('habilidades_requeridas', mode='before')
    @classmethod
    def parse_habilidades_requeridas(cls, v):
        """Convierte string CSV a lista de habilidades."""
        if v is None:
            return None
        if isinstance(v, str):
            habilidades = [h.strip() for h in v.split(',') if h.strip()]
            return habilidades if habilidades else None
        return v

    @field_validator('habilidades_deseables', mode='before')
    @classmethod
    def parse_habilidades_deseables(cls, v):
        """Convierte string CSV a lista de habilidades."""
        if v is None:
            return None
        if isinstance(v, str):
            habilidades = [h.strip() for h in v.split(',') if h.strip()]
            return habilidades if habilidades else None
        return v

    @field_validator('salario_maximo')
    @classmethod
    def validar_salario_maximo(cls, v, info):
        """Valida que el salario máximo no sea menor que el salario mínimo."""
        if v is not None and 'salario_minimo' in info.data and info.data['salario_minimo'] is not None:
            if v < info.data['salario_minimo']:
                raise ValueError('El salario máximo no puede ser menor que el salario mínimo')
        return v


class PerfilCargoResponse(PerfilCargoBase):
    """
    Esquema para responder con un perfil de cargo.
    """
    id: int
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
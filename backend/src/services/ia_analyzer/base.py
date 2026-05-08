"""
Interfaz base para el analizador de IA.
Permite cambiar entre diferentes proveedores (Deepseek, OpenAI, local) sin modificar el código de negocio.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List


@dataclass
class ResultadoAnalisis:
    """Resultado del análisis de un CV contra un perfil de cargo."""

    puntaje: int  # 0-100
    etiqueta: str  # "Recomendado", "Recomendado con reservas", "No Recomendado"
    feedback: str  # Retroalimentación detallada
    fortalezas: List[str]  # Lista de fortalezas encontradas
    debilidades: List[str]  # Lista de debilidades identificadas
    analisis_tecnico: dict  # Análisis técnico detallado en formato JSON
    razonamiento_inferencia: str  # Razonamiento paso a paso de la inferencia semántica
    puntaje_tecnico: int = 0  # Puntaje dimensional técnico
    puntaje_experiencia: int = 0  # Puntaje dimensional experiencia
    puntaje_soft_skills: int = 0  # Puntaje dimensional soft skills
    ponderado_final: int = 0  # Puntaje final con penalizaciones aplicadas
    reglas_negocio: List[str] = field(default_factory=list)  # Reglas de negocio aplicadas


class IAnalizadorIA(ABC):
    """
    Interfaz abstracta para el analizador de IA.
    Todos los proveedores (Deepseek, OpenAI, local) deben implementar esta interfaz.
    """

    @abstractmethod
    async def analizar_cv(
        self, cv_texto: str, perfil_titulo: str, perfil_descripcion: str, perfil_puntos_fuertes: List[str]
    ) -> ResultadoAnalisis:
        """
        Analiza un CV contra un perfil de cargo.

        Args:
            cv_texto: Texto extraído del CV.
            perfil_titulo: Título del perfil de cargo.
            perfil_descripcion: Descripción del perfil de cargo.
            perfil_puntos_fuertes: Lista de puntos fuertes/skills requeridos.

        Returns:
            ResultadoAnalisis con puntaje, etiqueta y feedback.

        Raises:
            AnalisisError: Si el análisis falla.
        """
        pass

    @abstractmethod
    async def verificar_conexion(self) -> bool:
        """
        Verifica si el proveedor de IA está disponible.

        Returns:
            True si está disponible, False si no.
        """
        pass


class AnalisisError(Exception):
    """Error durante el análisis de IA."""

    def __init__(self, mensaje: str, proveedor: str, causa: Exception | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.proveedor = proveedor
        self.causa = causa

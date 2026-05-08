"""
Módulo de servicios de análisis de IA para CVs.
"""
from .ia_analyzer.base import IAnalizadorIA
from .ia_analyzer.deepseek import DeepseekAdapter
from .ia_analyzer.local import LocalAdapter

__all__ = [
    "IAnalizadorIA",
    "DeepseekAdapter",
    "LocalAdapter",
]

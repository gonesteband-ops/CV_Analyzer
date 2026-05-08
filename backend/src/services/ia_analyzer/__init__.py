"""
Modulo de analisis de IA con arquitectura de adapters.
"""
from .base import IAnalizadorIA
from .deepseek import DeepseekAdapter
from .local import LocalAdapter
from .groq import GroqAdapter

__all__ = ["IAnalizadorIA", "DeepseekAdapter", "LocalAdapter", "GroqAdapter"]

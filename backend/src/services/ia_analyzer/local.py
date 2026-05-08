"""
Adapter local para análisis de CVs.
Usa embeddings y keyword matching como fallback cuando los proveedores externos no están disponibles.
"""
import logging
from typing import List

from .base import IAnalizadorIA, ResultadoAnalisis, AnalisisError

logger = logging.getLogger(__name__)


class LocalAdapter(IAnalizadorIA):
    """
    Adapter local que usa algoritmos de matching híbrido.
    Combina keyword matching (70%) + embeddings (30%) para el análisis.
    Sirve como fallback cuando Deepseek/OpenAI no están disponibles.
    """

    def __init__(self, modelo_embeddings: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa el adapter local.

        Args:
            modelo_embeddings: Nombre del modelo de embeddings a usar.
        """
        self.modelo_embeddings = modelo_embeddings
        self._modelo_cargado = None

    def _cargar_modelo(self):
        """Carga el modelo de embeddings si no está cargado."""
        if self._modelo_cargado is None:
            try:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Cargando modelo de embeddings: {self.modelo_embeddings}")
                self._modelo_cargado = SentenceTransformer(self.modelo_embeddings)
            except ImportError:
                logger.warning("sentence-transformers no disponible, usando solo keyword matching")
                self._modelo_cargado = False
            except Exception as e:
                logger.error(f"Error al cargar modelo de embeddings: {e}")
                self._modelo_cargado = False

    async def analizar_cv(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
        perfil=None,
    ) -> ResultadoAnalisis:
        """
        Analiza un CV usando enfoque híbrido local (embeddings + keywords).

        Algoritmo:
        1. Calcular similitud semántica con embeddings (70% del puntaje)
        2. Calcular coverage de keywords explícitas (30% del puntaje)
        3. Combinar: puntaje_final = 0.7 * embeddings + 0.3 * keywords
        """
        try:
            # Calcular similitud de embeddings (70%)
            similitud_embeddings = self._calcular_similitud_embeddings(
                cv_texto, perfil_descripcion, perfil_puntos_fuertes
            )

            # Calcular coverage de keywords (70%)
            coverage_keywords = self._calcular_coverage_keywords(cv_texto, perfil_puntos_fuertes)

            # Calcular puntaje combinado (30% embeddings, 70% keywords)
            puntaje_semantico = similitud_embeddings * 100  # 0-100
            puntaje_keywords = coverage_keywords * 100  # 0-100
            puntaje_final = int(0.3 * puntaje_semantico + 0.7 * puntaje_keywords)

            # Determinar etiqueta
            etiqueta = self._determinar_etiqueta(puntaje_final)

            # Generar feedback
            fortalezas, debilidades = self._generar_feedback(cv_texto, perfil_puntos_fuertes, puntaje_final)

            feedback = self._construir_feedback_narrativo(
                perfil_titulo, puntaje_final, fortalezas, debilidades
            )

            logger.info(f"Análisis local completado: puntaje={puntaje_final}, etiqueta={etiqueta}")

            return ResultadoAnalisis(
                puntaje=puntaje_final,
                etiqueta=etiqueta,
                feedback=feedback,
                fortalezas=fortalezas,
                debilidades=debilidades,
                analisis_tecnico={
                    "puntaje_experiencia": puntaje_final,
                    "puntaje_educacion": puntaje_final,
                    "puntaje_habilidades_tecnicas": puntaje_final,
                    "puntaje_habilidades_blandas": puntaje_final,
                    "anos_experiencia": 0,
                    "nivel_educativo": "No especificado",
                    "habilidades_directas_detectadas": fortalezas,
                    "habilidades_inferidas": [],
                    "habilidades_faltantes_criticas": debilidades,
                },
                razonamiento_inferencia="Análisis realizado con MatchingService local (baseline sin LLM).",
                puntaje_tecnico=puntaje_final,
                puntaje_experiencia=puntaje_final // 2,
                puntaje_soft_skills=puntaje_final // 2,
                ponderado_final=puntaje_final,
                reglas_negocio=[],
            )

        except Exception as e:
            logger.error(f"Error al analizar CV con adapter local: {e}")
            raise AnalisisError(
                mensaje="No se pudo analizar el CV con el adapter local",
                proveedor="Local",
                causa=e,
            )

    async def verificar_conexion(self) -> bool:
        """Verifica si el modelo local está disponible."""
        return True  # Siempre disponible

    def _calcular_similitud_embeddings(
        self, cv_texto: str, perfil_descripcion: str, perfil_puntos_fuertes: List[str]
    ) -> float:
        """
        Calcula similitud coseno entre embeddings del CV y perfil.

        Returns:
            Float entre 0 y 1 (1 = idéntico).
        """
        self._cargar_modelo()

        if self._modelo_cargado is False:
            # Fallback a solo keywords si no hay embeddings
            return 0.5

        try:
            from sentence_transformers import util

            # Construir texto del perfil
            perfil_texto = f"{perfil_descripcion}\n\nRequisitos: {', '.join(perfil_puntos_fuertes)}"

            # Generar embeddings
            embedding_cv = self._modelo_cargado.encode(cv_texto, convert_to_tensor=True)
            embedding_perfil = self._modelo_cargado.encode(perfil_texto, convert_to_tensor=True)

            # Calcular similitud coseno
            similitud = util.cos_sim(embedding_cv, embedding_perfil).item()

            # Normalizar a 0-1 (cos_sim puede ser negativo)
            return max(0, (similitud + 1) / 2)

        except Exception as e:
            logger.error(f"Error calculando embeddings: {e}")
            return 0.5

    def _calcular_coverage_keywords(self, cv_texto: str, perfil_puntos_fuertes: List[str]) -> float:
        """
        Calcula qué porcentaje de keywords del perfil aparecen en el CV.
        Usa word-boundary regex para evitar falsos positivos.

        Returns:
            Float entre 0 y 1 (1 = todas las keywords encontradas).
        """
        import re
        
        if not perfil_puntos_fuertes:
            return 1.0
        
        cv_texto_lower = cv_texto.lower()
        keywords_encontradas = 0
        
        for keyword in perfil_puntos_fuertes:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, cv_texto_lower):
                keywords_encontradas += 1
        
        return keywords_encontradas / len(perfil_puntos_fuertes)

    def _determinar_etiqueta(self, puntaje: int) -> str:
        """Determina la etiqueta basada en el puntaje."""
        if puntaje >= 70:
            return "Recomendado"
        elif puntaje >= 40:
            return "Recomendado con reservas"
        else:
            return "No Recomendado"

    def _generar_feedback(
        self, cv_texto: str, perfil_puntos_fuertes: List[str], puntaje: int
    ) -> tuple[List[str], List[str]]:
        """
        Genera listas de fortalezas y debilidades basadas en el análisis.
        Usa word-boundary regex para evitar falsos positivos.

        Returns:
            Tuple (fortalezas, debilidades)
        """
        import re
        
        fortalezas = []
        debilidades = []

        cv_texto_lower = cv_texto.lower()

        # Identificar fortalezas (keywords encontradas con word-boundary)
        for keyword in perfil_puntos_fuertes:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if re.search(pattern, cv_texto_lower):
                fortalezas.append(f"Posee {keyword.lower()}")

        # Si no hay fortalezas específicas, agregar genéricas
        if not fortalezas:
            if len(cv_texto) > 500:
                fortalezas.append("CV detallado y completo")
            else:
                fortalezas.append("CV presentado")

        # Identificar debilidades (keywords no encontradas con word-boundary)
        for keyword in perfil_puntos_fuertes:
            pattern = r'\b' + re.escape(keyword.lower()) + r'\b'
            if not re.search(pattern, cv_texto_lower):
                debilidades.append(f"No se menciona {keyword.lower()} en el CV")

        # Si el puntaje es bajo, agregar debilidad genérica
        if puntaje < 40 and not debilidades:
            debilidades.append("Experiencia insuficiente para el perfil")

        return fortalezas[:4], debilidades[:3]  # Limitar cantidades

    def _construir_feedback_narrativo(
        self, perfil_titulo: str, puntaje: int, fortalezas: List[str], debilidades: List[str]
    ) -> str:
        """Construye un párrafo de feedback narrativo."""
        if puntaje >= 70:
            nivel = "fuerte"
        elif puntaje >= 40:
            nivel = "parcial"
        else:
            nivel = "limitada"

        fortalezas_str = ", ".join(fortalezas[:2]) if fortalezas else "algunas competencias"
        debilidades_str = ", ".join(debilidades[:2]) if debilidades else "áreas por desarrollar"

        return (
            f"El candidato muestra una coincidencia {nivel} con el perfil de {perfil_titulo}. "
            f"Entre sus fortalezas destacan: {fortalezas_str}. "
            f"Se identifican áreas de mejora en: {debilidades_str}. "
            f"Puntaje final: {puntaje}/100."
        )

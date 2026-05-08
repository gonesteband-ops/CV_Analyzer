"""
Servicio de matching híbrido para CVs.
Combina keywords (70%) + embeddings (30%) para análisis de candidatos.
"""
import re
import logging
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ResultadoMatching:
    """Resultado del matching entre CV y perfil."""

    puntaje_semantico: float  # 0-1 (embeddings)
    puntaje_keywords: float   # 0-1 (keywords)
    puntaje_final: int        # 0-100 (combinado)
    keywords_encontradas: List[str]
    keywords_faltantes: List[str]
    similitud_coseno: float   # Similitud de coseno raw


class MatchingService:
    """
    Servicio de matching híbrido para análisis de CVs.

    Algoritmo:
    - 70% Coverage de keywords explícitas (presencia real de términos)
    - 30% Similitud semántica (embeddings de sentence-transformers)

    Esto permite:
    - Asegurar que requisitos técnicos específicos se detecten literalmente
    - Capturar significado contextual (sinónimos, conceptos relacionados) como factor secundario
    - Evitar falsos positivos por coincidencias semánticas genéricas
    """

    # Pesos del algoritmo híbrido (INVERTIDOS: más peso a keywords)
    PESO_EMBEDDINGS = 0.3
    PESO_KEYWORDS = 0.7
    
    # Umbrales por defecto (pueden ser override por perfil)
    UMBRAL_RECOMENDADO = 70
    UMBRAL_RESERVAS = 40
    
    def __init__(self, modelo_embeddings: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"):
        """
        Inicializa el servicio de matching.
        
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
                logger.info("Modelo de embeddings cargado exitosamente")
                
            except ImportError as e:
                logger.warning(f"sentence-transformers no disponible: {e}")
                self._modelo_cargado = False
            except Exception as e:
                logger.error(f"Error al cargar modelo de embeddings: {e}")
                self._modelo_cargado = False
    
    def calcular_matching(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
        umbral_recomendado: int = None,
        umbral_reservas: int = None,
    ) -> ResultadoMatching:
        """
        Calcula el matching entre un CV y un perfil de cargo.
        
        Args:
            cv_texto: Texto extraído del CV.
            perfil_titulo: Título del perfil de cargo.
            perfil_descripcion: Descripción del perfil.
            perfil_puntos_fuertes: Lista de skills/puntos fuertes requeridos.
            umbral_recomendado: Puntaje mínimo para "Recomendado" (default: 70).
            umbral_reservas: Puntaje mínimo para "Recomendado con reservas" (default: 40).
            
        Returns:
            ResultadoMatching con puntajes y keywords encontradas/faltantes.
        """
        # Calcular similitud de embeddings (70%)
        similitud_embeddings = self._calcular_similitud_embeddings(
            cv_texto,
            perfil_descripcion,
            perfil_puntos_fuertes,
        )
        
        # Calcular coverage de keywords (30%)
        coverage_keywords, keywords_encontradas, keywords_faltantes = self._calcular_coverage_keywords(
            cv_texto,
            perfil_puntos_fuertes,
        )
        
        # Calcular puntaje combinado
        puntaje_semantico = similitud_embeddings  # 0-1
        puntaje_keywords = coverage_keywords  # 0-1
        
        puntaje_final = int(
            (self.PESO_EMBEDDINGS * puntaje_semantico + self.PESO_KEYWORDS * puntaje_keywords) * 100
        )
        
        # Clamp a 0-100
        puntaje_final = max(0, min(100, puntaje_final))
        
        logger.info(
            f"Matching completado: semántico={puntaje_semantico:.2f}, "
            f"keywords={puntaje_keywords:.2f}, final={puntaje_final}"
        )
        
        return ResultadoMatching(
            puntaje_semantico=puntaje_semantico,
            puntaje_keywords=puntaje_keywords,
            puntaje_final=puntaje_final,
            keywords_encontradas=keywords_encontradas,
            keywords_faltantes=keywords_faltantes,
            similitud_coseno=similitud_embeddings,
        )
    
    def _calcular_similitud_embeddings(
        self,
        cv_texto: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
    ) -> float:
        """
        Calcula similitud de coseno entre embeddings del CV y perfil.
        
        Args:
            cv_texto: Texto del CV.
            perfil_descripcion: Descripción del perfil.
            perfil_puntos_fuertes: Skills requeridos.
            
        Returns:
            Float entre 0 y 1 (1 = idéntico).
        """
        self._cargar_modelo()
        
        # Fallback si el modelo no está disponible
        if self._modelo_cargado is False:
            logger.warning("Usando fallback de similitud (0.5) por falta de embeddings")
            return 0.5
        
        try:
            from sentence_transformers import util
            import torch
            
            # Construir texto completo del perfil
            perfil_texto = self._construir_texto_perfil(
                perfil_descripcion,
                perfil_puntos_fuertes,
            )
            
            # Tokenizar textos (limitar longitud para evitar OOM)
            cv_texto_truncado = cv_texto[:5000] if len(cv_texto) > 5000 else cv_texto
            perfil_texto_truncado = perfil_texto[:1000] if len(perfil_texto) > 1000 else perfil_texto
            
            # Generar embeddings
            embedding_cv = self._modelo_cargado.encode(
                cv_texto_truncado,
                convert_to_tensor=True,
                show_progress_bar=False,
            )
            embedding_perfil = self._modelo_cargado.encode(
                perfil_texto_truncado,
                convert_to_tensor=True,
                show_progress_bar=False,
            )
            
            # Calcular similitud de coseno
            similitud = util.cos_sim(embedding_cv, embedding_perfil).item()
            
            # Normalizar a 0-1 (cos_sim puede ser negativo en el rango -1 a 1)
            similitud_normalizada = max(0, (similitud + 1) / 2)
            
            logger.debug(f"Similitud de coseno raw: {similitud:.4f}, normalizada: {similitud_normalizada:.4f}")
            
            return similitud_normalizada
            
        except Exception as e:
            logger.error(f"Error calculando embeddings: {e}")
            return 0.5  # Fallback neutral
    
    def _calcular_coverage_keywords(
        self,
        cv_texto: str,
        perfil_puntos_fuertes: List[str],
    ) -> tuple[float, List[str], List[str]]:
        """
        Calcula qué porcentaje de keywords del perfil aparecen en el CV.
        Usa word-boundary regex para evitar falsos positivos.

        Args:
            cv_texto: Texto del CV.
            perfil_puntos_fuertes: Skills requeridos.

        Returns:
            Tuple[float, List[str], List[str]]: (coverage, encontradas, faltantes)
        """
        import re
        
        if not perfil_puntos_fuertes:
            return 1.0, [], []
        
        cv_texto_lower = cv_texto.lower()
        keywords_encontradas = []
        keywords_faltantes = []
        
        for keyword in perfil_puntos_fuertes:
            keyword_lower = keyword.lower()
            
            # MATCH EXACTO: la keyword debe aparecer como término completo
            # Usa word boundaries para evitar falsos positivos
            pattern = r'\b' + re.escape(keyword_lower) + r'\b'
            if re.search(pattern, cv_texto_lower):
                keywords_encontradas.append(keyword)
            else:
                keywords_faltantes.append(keyword)
        
        coverage = len(keywords_encontradas) / len(perfil_puntos_fuertes)
        
        logger.debug(
            f"Keywords: {len(keywords_encontradas)}/{len(perfil_puntos_fuertes)} "
            f"encontradas (coverage: {coverage:.2f})"
        )
        
        return coverage, keywords_encontradas, keywords_faltantes
    
    def _construir_texto_perfil(
        self,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
    ) -> str:
        """
        Construye el texto completo del perfil para embeddings.
        
        Args:
            perfil_descripcion: Descripción del perfil.
            perfil_puntos_fuertes: Skills requeridos.
            
        Returns:
            str: Texto combinado para embedding.
        """
        texto = perfil_descripcion
        
        if perfil_puntos_fuertes:
            texto += "\n\nRequisitos principales: " + ", ".join(perfil_puntos_fuertes)
        
        return texto
    
    def determinar_etiqueta(
        self,
        puntaje: int,
        umbral_recomendado: int = None,
        umbral_reservas: int = None,
    ) -> str:
        """
        Determina la etiqueta de recomendación basada en el puntaje.
        
        Args:
            puntaje: Puntaje final (0-100).
            umbral_recomendado: Puntaje mínimo para "Recomendado".
            umbral_reservas: Puntaje mínimo para "Recomendado con reservas".
            
        Returns:
            str: "Recomendado", "Recomendado con reservas", o "No Recomendado"
        """
        umbral_rec = umbral_recomendado or self.UMBRAL_RECOMENDADO
        umbral_res = umbral_reservas or self.UMBRAL_RESERVAS
        
        if puntaje >= umbral_rec:
            return "Recomendado"
        elif puntaje >= umbral_res:
            return "Recomendado con reservas"
        else:
            return "No Recomendado"
    
    def generar_feedback(
        self,
        cv_texto: str,
        perfil_titulo: str,
        resultado_matching: ResultadoMatching,
    ) -> tuple[List[str], List[str], str]:
        """
        Genera feedback detallado basado en el resultado del matching.
        Usa lenguaje preciso que refleja presencia de keywords sin afirmar categóricamente.

        Args:
            cv_texto: Texto del CV.
            perfil_titulo: Título del perfil.
            resultado_matching: Resultado del matching.

        Returns:
            Tuple[List[str], List[str], str]: (fortalezas, debilidades, feedback_narrativo)
        """
        fortalezas = []
        debilidades = []

        # Generar fortalezas basadas en keywords encontradas (solo match exacto validado)
        for keyword in resultado_matching.keywords_encontradas[:3]:  # Máximo 3
            fortalezas.append(f"Posee {keyword.lower()}")

        # Si no hay fortalezas de keywords pero el puntaje semántico es alto, agregar nota contextual
        if not fortalezas and resultado_matching.puntaje_semantico > 0.7:
            fortalezas.append("Perfil con afinidad semántica al cargo")
        elif not fortalezas:
            if len(cv_texto) > 1000:
                fortalezas.append("Experiencia detallada en el CV")
            else:
                fortalezas.append("CV presentado correctamente")

        # Generar debilidades basadas en keywords faltantes
        for keyword in resultado_matching.keywords_faltantes[:2]:  # Máximo 2
            debilidades.append(f"No se menciona {keyword.lower()} en el CV")

        # Si el puntaje es bajo, agregar debilidad genérica
        if resultado_matching.puntaje_final < 40 and not debilidades:
            debilidades.append("Experiencia insuficiente para el perfil")

        # Construir feedback narrativo
        feedback = self._construir_feedback_narrativo(
            perfil_titulo,
            resultado_matching.puntaje_final,
            fortalezas,
            debilidades,
            resultado_matching.puntaje_semantico,
            resultado_matching.puntaje_keywords,
        )

        return fortalezas, debilidades, feedback
    
    def _construir_feedback_narrativo(
        self,
        perfil_titulo: str,
        puntaje_final: int,
        fortalezas: List[str],
        debilidades: List[str],
        puntaje_semantico: float,
        puntaje_keywords: float,
    ) -> str:
        """
        Construye un párrafo de feedback narrativo con lenguaje preciso.

        Args:
            perfil_titulo: Título del perfil.
            puntaje_final: Puntaje combinado (0-100).
            fortalezas: Lista de fortalezas.
            debilidades: Lista de debilidades.
            puntaje_semantico: Puntaje de embeddings (0-1).
            puntaje_keywords: Puntaje de keywords (0-1).

        Returns:
            str: Feedback narrativo.
        """
        # Determinar nivel de coincidencia
        if puntaje_final >= 70:
            nivel = "fuerte"
        elif puntaje_final >= 40:
            nivel = "parcial"
        else:
            nivel = "limitada"

        fortalezas_str = ", ".join(fortalezas[:2]) if fortalezas else "algunas competencias"
        debilidades_str = ", ".join(debilidades[:2]) if debilidades else "áreas por desarrollar"

        # Construir narrativa
        feedback = (
            f"El análisis del CV muestra una coincidencia {nivel} con el perfil de {perfil_titulo}. "
        )

        # Agregar contexto de keywords (más relevante)
        if puntaje_keywords > 0.7:
            feedback += "El CV contiene la mayoría de las competencias técnicas requeridas. "
        elif puntaje_keywords > 0.4:
            feedback += "Se identifican algunas competencias técnicas del perfil. "
        else:
            feedback += "El CV no evidencia las competencias técnicas principales requeridas. "

        # Agregar contexto semántico (secundario)
        if puntaje_semantico > 0.7:
            feedback += "La redacción de la experiencia es consistente con el perfil. "
        elif puntaje_semantico > 0.4:
            feedback += "Presenta algunas similitudes en la descripción de experiencias. "

        # Agregar fortalezas (con lenguaje preciso)
        feedback += f"Se identifica: {fortalezas_str}. "

        # Agregar debilidades
        if debilidades:
            feedback += f"Falta evidenciar: {debilidades_str}. "

        # Cierre con puntaje
        feedback += f"Puntaje final: {puntaje_final}/100."

        return feedback

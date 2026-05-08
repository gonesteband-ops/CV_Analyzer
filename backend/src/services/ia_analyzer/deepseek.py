"""
Adapter para Deepseek AI.
Proveedor económico para análisis de CVs.
"""
import logging
from typing import List

from .base import IAnalizadorIA, ResultadoAnalisis, AnalisisError

logger = logging.getLogger(__name__)


class DeepseekAdapter(IAnalizadorIA):
    """
    Adapter para el proveedor Deepseek AI.
    Implementa la interfaz IAnalizadorIA para análisis de CVs.
    """

    def __init__(self, api_key: str, modelo: str = "deepseek-chat"):
        """
        Inicializa el adapter de Deepseek.

        Args:
            api_key: Clave de API de Deepseek.
            modelo: Nombre del modelo a usar.
        """
        self.api_key = api_key
        self.modelo = modelo
        self.base_url = "https://api.deepseek.com/v1"

    async def analizar_cv(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
        perfil=None,
    ) -> ResultadoAnalisis:
        """
        Analiza un CV usando Deepseek AI.

        El prompt está diseñado para obtener:
        - Puntaje 0-100 basado en matching semántico
        - Etiqueta de recomendación
        - Fortalezas y debilidades basadas en competencias explícitas
        - Justificación técnica
        """
        try:
            import json
            from httpx import AsyncClient, Timeout

            # Construir prompt para el análisis
            prompt = self._construir_prompt(
                cv_texto, perfil_titulo, perfil_descripcion, perfil_puntos_fuertes
            )

            logger.info(f"Analizando CV con Deepseek modelo={self.modelo}")

            # Llamar a API de Deepseek
            async with AsyncClient(timeout=Timeout(timeout=60.0)) as client:
                response = await client.post(
                    self.base_url + "/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.modelo,
                        "messages": [
                            {
                                "role": "system",
                                "content": "Eres un Auditor Senior de Talento y Experto en Inferencia Semántica. Tu objetivo principal es detectar el potencial latente en los currículums mediante la 'Teoría de Transferencia de Competencias'. REGLA CRÍTICA: No busques coincidencias literales. Si el candidato menciona una herramienta, cargo, métrica o industria que pertenece a un ecosistema técnico superior, DEBES inferir y validar automáticamente las habilidades subyacentes. (Ejemplo: 'Gestión de Call Center' implica manejo de KPIs, resolución de conflictos y CRM; 'Power BI' implica DAX y modelamiento de datos). Debes pensar paso a paso y responder ÚNICAMENTE con un objeto JSON válido."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 2500,
                        "response_format": {"type": "json_object"}
                    }
                )
                response.raise_for_status()

            # Parsear respuesta
            data = response.json()
            contenido = data["choices"][0]["message"]["content"].strip()

            # Extraer JSON del contenido (puede estar envuelto en ```json ... ```)
            if contenido.startswith("```"):
                contenido = contenido.split("```")[1]
                if contenido.startswith("json"):
                    contenido = contenido[4:]
            contenido = contenido.strip()

            # Parsear JSON
            resultado_json = json.loads(contenido)

            logger.info(f"Razonamiento inferencia: {resultado_json.get('razonamiento_inferencia')}")
            logger.info(f"Análisis completado: puntaje={resultado_json.get('puntaje')}, etiqueta={resultado_json.get('etiqueta')}")

            # Construir ResultadoAnalisis
            return ResultadoAnalisis(
                puntaje=resultado_json.get("puntaje", 50),
                etiqueta=resultado_json.get("etiqueta", "No Recomendado"),
                feedback=resultado_json.get("justificacion", "Sin justificación disponible"),
                fortalezas=resultado_json.get("fortalezas", []),
                debilidades=resultado_json.get("debilidades", []),
                analisis_tecnico=resultado_json.get("analisis_tecnico", {}),
                razonamiento_inferencia=resultado_json.get("razonamiento_inferencia", ""),
                puntaje_tecnico=resultado_json.get("puntaje_tecnico", 0),
                puntaje_experiencia=resultado_json.get("puntaje_experiencia", 0),
                puntaje_soft_skills=resultado_json.get("puntaje_soft_skills", 0),
                ponderado_final=resultado_json.get("ponderado_final", 0),
                reglas_negocio=resultado_json.get("reglas_negocio", []),
            )

        except Exception as e:
            logger.error(f"Error al analizar CV con Deepseek: {e}")
            raise AnalisisError(
                mensaje="No se pudo analizar el CV con Deepseek",
                proveedor="Deepseek",
                causa=e,
            )

    async def verificar_conexion(self) -> bool:
        """Verifica si la API de Deepseek está disponible."""
        try:
            # TODO: Implementar health check real a la API
            logger.info("Verificando conexión con Deepseek API")
            return True
        except Exception as e:
            logger.error(f"Error al verificar conexión con Deepseek: {e}")
            return False

    def _construir_prompt(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
    ) -> str:
        """
        Construye el prompt para enviar a Deepseek.

        Args:
            cv_texto: Texto del CV.
            perfil_titulo: Título del perfil.
            perfil_descripcion: Descripción del perfil.
            perfil_puntos_fuertes: Skills requeridos.

        Returns:
            Prompt formateado para el análisis.
        """
        puntos_fuertes_str = "\n".join(f"- {punto}" for punto in perfil_puntos_fuertes)

        return f"""
Evalua al candidato contra el perfil del cargo mediante la Teoría de Transferencia de Competencias.

**Perfil**
Titulo: {perfil_titulo}
Descripcion: {perfil_descripcion}
Competencias requeridas:
{puntos_fuertes_str}

**CV**
{cv_texto[:12000]}

REGLAS ESTRICTAS DE INFERENCIA SEMÁNTICA:

1. **TRANSFERENCIA DE COMPETENCIAS**: No busques coincidencias literales. Si el candidato menciona una herramienta, cargo, métrica o industria que pertenece a un ecosistema técnico superior, DEBES inferir automáticamente las habilidades subyacentes.
   - Ejemplo: 'Gestión de Call Center' → implica KPIs, resolución de conflictos, CRM
   - Ejemplo: 'Power BI' → implica DAX, modelamiento de datos, SQL
   - Ejemplo: 'Jefe de equipo' → implica liderazgo, gestión de personas, delegación
   - Ejemplo: 'Atención al cliente' → implica comunicación asertiva, negociación, CRM

2. **MAPEO SEMÁNTICO**: Antes de asignar puntajes, debes realizar un análisis paso a paso relacionando cada experiencia del CV con las competencias requeridas.

3. **SOBRECALIFICACION**: Evalua si los años de experiencia EXCEDEN significativamente lo esperado para el nivel del cargo.

4. **EDUCACION**: Compara la formación del candidato con lo requerido.

Responde ÚNICAMENTE con este objeto JSON, respetando el orden de las claves:

{{
  "razonamiento_inferencia": "ANALISIS OBLIGATORIO PASO A PASO. Escribe aquí tu mapeo semántico. Relaciona la experiencia del CV con las competencias requeridas. Explica qué habilidades implícitas detectaste a partir de las herramientas o cargos mencionados.",
  "puntaje": 0-100,
  "etiqueta": "Recomendado" | "Recomendado con reservas" | "No Recomendado",
  "analisis_tecnico": {{
    "puntaje_experiencia": 0-100,
    "puntaje_educacion": 0-100,
    "puntaje_habilidades_tecnicas": 0-100,
    "puntaje_habilidades_blandas": 0-100,
    "anos_experiencia": numero,
    "nivel_educativo": "string",
    "habilidades_directas_detectadas": ["skill1", "skill2"],
    "habilidades_inferidas": ["skill implícita 1", "skill implícita 2"],
    "habilidades_faltantes_criticas": ["skill1"]
  }},
  "fortalezas": ["fortaleza específica 1", "fortaleza específica 2"],
  "debilidades": ["debilidad real, no inventada"],
  "justificacion": "Resumen ejecutivo del porqué de la decisión final."
}}
"""

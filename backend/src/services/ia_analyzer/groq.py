"""
Adapter para GROQ AI.
Usa API compatible con OpenAI (https://api.groq.com/openai/v1).
Sin filtros restrictivos de contenido, ideal para analisis de CVs en espanol.
"""
import logging
from typing import List

from .base import IAnalizadorIA, ResultadoAnalisis, AnalisisError

logger = logging.getLogger(__name__)


class GroqAdapter(IAnalizadorIA):
    """
    Adapter para el proveedor GROQ AI.
    Implementa la interfaz IAnalizadorIA para analisis de CVs con LLM-Reasoning.
    """

    def __init__(self, api_key: str, modelo: str = "llama-3.3-70b-versatile"):
        self.api_key = api_key
        self.modelo = modelo
        self.base_url = "https://api.groq.com/openai/v1"

    async def analizar_cv(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
        perfil=None,
    ) -> ResultadoAnalisis:
        try:
            import json
            import re
            from httpx import AsyncClient, Timeout

            # Sanitizar texto del CV para evitar errores 400 en JSON
            texto_limpio = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"]', '', cv_texto[:12000])
            texto_limpio = texto_limpio.encode('utf-8', errors='ignore').decode('utf-8')

            prompt = self._construir_prompt(
                texto_limpio, perfil_titulo, perfil_descripcion, perfil_puntos_fuertes
            )

            logger.info(f"Analizando CV con GROQ modelo={self.modelo}")

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
                                "content": "Eres un Auditor Senior de Talento y Experto en Inferencia Semántica. Tu objetivo es analizar currículums comparándolos con perfiles de cargo. REGLAS CRÍTICAS: 1) Debes responder ÚNICAMENTE con un objeto JSON válido, sin texto adicional. 2) No busques coincidencias literales. Infiere habilidades implícitas usando la 'Teoría de Transferencia de Competencias'. 3) Si el candidato menciona una herramienta, cargo o métrica, infiere automáticamente las habilidades subyacentes. PENALIZACIONES OBLIGATORIAS: sobrecalificado DEBE ser true si el candidato tiene MUCHA MÁS experiencia o especialización de la que el cargo requiere (ej: Senior con 10 años postulando a Junior). cambio_rubro DEBE ser true si el candidato viene de una industria COMPLETAMENTE DIFERENTE al del cargo (ej: ingeniero de datos postulando a atención al cliente)."
                            },
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ],
                        "temperature": 0,
                        "max_tokens": 2500
                    }
                )
                response.raise_for_status()

            data = response.json()
            contenido = data["choices"][0]["message"]["content"].strip()

            if contenido.startswith("```"):
                contenido = contenido.split("```")[1]
                if contenido.startswith("json"):
                    contenido = contenido[4:]
            contenido = contenido.strip()

            resultado_json = json.loads(contenido)

            logger.info(f"Razonamiento inferencia: {resultado_json.get('razonamiento_inferencia')}")
            logger.info(f"Analisis tecnico: {resultado_json.get('analisis_tecnico')}")

            # Calcular ponderado final con pesos del perfil
            if perfil:
                peso_tecnico = (getattr(perfil, 'peso_tecnico', 50) or 50) / 100.0
                peso_experiencia = (getattr(perfil, 'peso_experiencia', 30) or 30) / 100.0
                peso_soft_skills = (getattr(perfil, 'peso_soft_skills', 20) or 20) / 100.0
            else:
                peso_tecnico = 0.5
                peso_experiencia = 0.3
                peso_soft_skills = 0.2

            # Usar puntaje general como base, o los dimensionales si existen
            puntaje_general = resultado_json.get("puntaje", 50)
            puntaje_tecnico = resultado_json.get("puntaje_tecnico", puntaje_general)
            puntaje_experiencia = resultado_json.get("puntaje_experiencia", puntaje_general)
            puntaje_soft_skills = resultado_json.get("puntaje_soft_skills", puntaje_general)

            # Penalizaciones configurables del perfil
            if perfil:
                penalizacion_sobre = getattr(perfil, 'penalizacion_sobrecalificado', 25) or 25
                penalizacion_rubro = getattr(perfil, 'penalizacion_cambio_rubro', 15) or 15
            else:
                penalizacion_sobre = 25
                penalizacion_rubro = 15
            
            penalizacion = 0
            reglas_aplicadas = []
            if resultado_json.get("sobrecalificado"):
                penalizacion += penalizacion_sobre
                reglas_aplicadas.append(f"Candidato sobrecalificado (-{penalizacion_sobre} puntos)")
            if resultado_json.get("cambio_rubro"):
                penalizacion += penalizacion_rubro
                reglas_aplicadas.append(f"Cambio de rubro no coherente (-{penalizacion_rubro} puntos)")

            ponderado = (
                puntaje_tecnico * peso_tecnico +
                puntaje_experiencia * peso_experiencia +
                puntaje_soft_skills * peso_soft_skills
            ) - penalizacion

            ponderado_final = max(0, min(100, int(ponderado)))

            return ResultadoAnalisis(
                puntaje=ponderado_final,
                etiqueta=resultado_json.get("etiqueta", "No recomendado"),
                feedback=resultado_json.get("justificacion", "Sin justificacion disponible"),
                fortalezas=resultado_json.get("fortalezas", []),
                debilidades=resultado_json.get("debilidades", []),
                analisis_tecnico=resultado_json.get("analisis_tecnico", {}),
                razonamiento_inferencia=resultado_json.get("razonamiento_inferencia", ""),
                puntaje_tecnico=puntaje_tecnico,
                puntaje_experiencia=puntaje_experiencia,
                puntaje_soft_skills=puntaje_soft_skills,
                ponderado_final=ponderado_final,
                reglas_negocio=reglas_aplicadas,
            )

        except Exception as e:
            logger.error(f"Error al analizar CV con GROQ: {e}")
            raise AnalisisError(
                mensaje="No se pudo analizar el CV con GROQ",
                proveedor="GROQ",
                causa=e,
            )

    async def verificar_conexion(self) -> bool:
        try:
            from httpx import AsyncClient, Timeout
            async with AsyncClient(timeout=Timeout(timeout=10.0)) as client:
                response = await client.get(
                    self.base_url + "/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Error al verificar conexion con GROQ: {e}")
            return False

    def _construir_prompt(
        self,
        cv_texto: str,
        perfil_titulo: str,
        perfil_descripcion: str,
        perfil_puntos_fuertes: List[str],
    ) -> str:
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

3. **SOBRECALIFICACION (PENALIZACION OBLIGATORIA)**: Evalua si los años de experiencia EXCEDEN significativamente lo esperado para el nivel del cargo.
   - Ejemplo: Candidato con 10 años de experiencia postulando a cargo Junior (1-2 años) → sobrecalificado = true
   - Ejemplo: Candidato con 8 años en cargo Senior postulando a cargo Trainee → sobrecalificado = true
   - Si el candidato calza bien con el nivel del cargo → sobrecalificado = false

4. **CAMBIO DE RUBRO (PENALIZACION OBLIGATORIA)**: Evalua si el candidato viene de una industria COMPLETAMENTE DIFERENTE al del cargo.
   - Ejemplo: Ingeniero de datos (analytics) postulando a Atención al Cliente → cambio_rubro = true
   - Ejemplo: Ejecutivo de ventas B2B postulando a Ejecutivo de cobranzas → cambio_rubro = false (mismo rubro comercial)
   - Si el candidato tiene experiencia en el rubro → cambio_rubro = false

5. **EDUCACION**: Compara la formación del candidato con lo requerido.

Responde ÚNICAMENTE con este objeto JSON, respetando el orden de las claves:

{{
  "puntaje_tecnico": 0-100,
  "puntaje_experiencia": 0-100,
  "puntaje_soft_skills": 0-100,
  "puntaje_general": 0-100,
  "sobrecalificado": true o false (DEBES evaluar esto obligatoriamente),
  "cambio_rubro": true o false (DEBES evaluar esto obligatoriamente),
  "razonamiento_inferencia": "ANALISIS OBLIGATORIO PASO A PASO. Escribe aquí tu mapeo semántico. Relaciona la experiencia del CV con las competencias requeridas. Explica qué habilidades implícitas detectaste a partir de las herramientas o cargos mencionados. INCLUYE tu evaluación de sobrecalificado y cambio_rubro.",
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
  "justificacion": "Resumen ejecutivo del porqué de la decisión final. Si aplicó sobrecalificado o cambio_rubro, MENCIONALO EXPLICITAMENTE aquí."
}}
"""
    
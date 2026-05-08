"""
Servicio de extracción de información de CVs usando IA.
Extrae: Nombre, Email y Resumen del perfil.
"""
import logging
import re
from dataclasses import dataclass
from typing import Optional

from .ia_analyzer.base import IAnalizadorIA, AnalisisError
from .cv_parser import CVParser

logger = logging.getLogger(__name__)


@dataclass
class InformacionCV:
    """Información extraída de un CV."""

    nombre: Optional[str] = None
    email: Optional[str] = None
    resumen: Optional[str] = None
    telefono: Optional[str] = None
    texto_completo: str = ""


class ExtractorCVError(Exception):
    """Error al extraer información de un CV."""

    def __init__(self, mensaje: str, causa: Exception | None = None):
        super().__init__(mensaje)
        self.causa = causa


class ExtractorCV:
    """
    Servicio para extraer información clave de CVs.

    Usa combinación de:
    1. Expresiones regulares para datos estructurados (email, teléfono)
    2. IA para datos no estructurados (nombre, resumen)
    """

    # Patrón para email
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'

    # Patrón para teléfono (formato Chile)
    TELEFONO_PATTERN = r'(?:\+56|56)?(?:9)?(\d{8})|\+56\s?9\s?\d{4}\s?\d{4}|(\d{2,3})\s?(\d{3,4})\s?(\d{3,4})'

    def __init__(self, analizador_ia: IAnalizadorIA | None = None):
        """
        Inicializa el extractor.

        Args:
            analizador_ia: Instancia del analizador de IA (opcional, usa local por defecto).
        """
        self.parser = CVParser()
        self.analizador_ia = analizador_ia

    def extraer_informacion_sync(self, archivo_path: str) -> InformacionCV:
        """
        Extrae información clave de un archivo CV (versión SÍNCRONA).

        Args:
            archivo_path: Ruta al archivo del CV.

        Returns:
            InformacionCV con los datos extraídos.

        Raises:
            ExtractorCVError: Si falla la extracción.
        """
        try:
            logger.info(f"Extrayendo información de: {archivo_path}")

            # Extraer texto del CV
            texto, tipo = self.parser.extraer_texto(archivo_path)
            logger.info(f"Texto extraído ({tipo}): {len(texto)} caracteres")

            # Crear resultado base
            resultado = InformacionCV(texto_completo=texto)

            # Extraer datos con regex (rápido, sin IA)
            resultado.email = self._extraer_email(texto)
            resultado.telefono = self._extraer_telefono(texto)
            logger.info(f"Email encontrado: {resultado.email}")

            # Extraer nombre y resumen
            if texto.strip():
                # Intentar con IA primero si está disponible
                if self.analizador_ia:
                    try:
                        # Usamos la versión async pero la ejecutamos de forma síncrona
                        # Esto es un placeholder, ya que no tenemos un método sync en IAnalizadorIA.
                        # En la práctica, se usará el fallback o se implementará un wrapper.
                        # Por ahora, usamos el fallback para mantener la consistencia.
                        resultado.nombre, resultado.resumen = self._extraer_con_ia_sync(texto)[:2]
                        # El teléfono ya se extrajo con regex arriba, así que no lo sobrescribimos aquí
                    except Exception as e:
                        logger.warning(f"Error al usar IA para extracción: {e}. Usando fallback.")
                        resultado.nombre, resultado.resumen, telefono_fallback = self._extraer_con_ia_sync(texto)
                        if not resultado.telefono:
                            resultado.telefono = telefono_fallback
                else:
                    resultado.nombre, resultado.resumen, telefono_fallback = self._extraer_con_ia_sync(texto)
                    if not resultado.telefono:
                        resultado.telefono = telefono_fallback
            else:
                logger.warning(f"CV {archivo_path} está vacío")
                resultado.nombre = None
                resultado.resumen = "CV sin contenido extraíble"

            logger.info(f"Información extraída: nombre={resultado.nombre}, email={resultado.email}")
            return resultado

        except Exception as e:
            logger.error(f"Error al extraer información de {archivo_path}: {e}", exc_info=True)
            raise ExtractorCVError(f"No se pudo extraer información del CV: {str(e)}", e)

    async def extraer_informacion(self, archivo_path: str) -> InformacionCV:
        """
        Extrae información clave de un archivo CV.

        Args:
            archivo_path: Ruta al archivo del CV.

        Returns:
            InformacionCV con los datos extraídos.

        Raises:
            ExtractorCVError: Si falla la extracción.
        """
        try:
            logger.info(f"Extrayendo información de: {archivo_path}")
            
            # Extraer texto del CV
            texto, tipo = self.parser.extraer_texto(archivo_path)
            logger.info(f"Texto extraído ({tipo}): {len(texto)} caracteres")

            # Crear resultado base
            resultado = InformacionCV(texto_completo=texto)

            # Extraer datos con regex (rápido, sin IA)
            resultado.email = self._extraer_email(texto)
            resultado.telefono = self._extraer_telefono(texto)
            logger.info(f"Email encontrado: {resultado.email}")

            # Extraer nombre y resumen con IA
            if texto.strip():
                resultado.nombre, resultado.resumen = await self._extraer_con_ia(texto)
            else:
                logger.warning(f"CV {archivo_path} está vacío")
                resultado.nombre = None
                resultado.resumen = "CV sin contenido extraíble"

            logger.info(f"Información extraída: nombre={resultado.nombre}, email={resultado.email}")
            return resultado

        except Exception as e:
            logger.error(f"Error al extraer información de {archivo_path}: {e}", exc_info=True)
            raise ExtractorCVError(f"No se pudo extraer información del CV: {str(e)}", e)

    def _extraer_email(self, texto: str) -> Optional[str]:
        """
        Extrae el primer email encontrado en el texto.

        Args:
            texto: Texto del CV.

        Returns:
            Email encontrado o None.
        """
        emails = re.findall(self.EMAIL_PATTERN, texto, re.IGNORECASE)
        return emails[0].lower() if emails else None

    def _extraer_telefono(self, texto: str) -> Optional[str]:
        """
        Extrae el primer teléfono encontrado en el texto.

        Args:
            texto: Texto del CV.

        Returns:
            Teléfono encontrado o None.
        """
        match = re.search(self.TELEFONO_PATTERN, texto)
        if match:
            # Normalizar formato
            grupos = match.groups()
            if grupos[0]:  # Formato 9XXXXXXXX
                return f"+56 9 {grupos[0][:4]} {grupos[0][4:]}"
            elif grupos[1]:  # Formato XXX XXX XXXX
                return f"+56 {grupos[1]} {grupos[2]} {grupos[3]}"
        return None

    def _extraer_con_ia_sync(self, texto: str) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Extrae nombre, resumen y teléfono del perfil (versión SÍNCRONA).

        Usa extracción básica con regex/heurísticas cuando no hay IA disponible.

        Args:
            texto: Texto completo del CV.

        Returns:
            Tuple con (nombre, resumen, telefono).
        """
        logger.info("Usando extracción básica (sin IA)")
        nombre = self._extraer_nombre_basico(texto)
        resumen = self._generar_resumen_basico(texto)
        telefono = self._extraer_telefono(texto)
        return nombre, resumen, telefono

    async def _extraer_con_ia(self, texto: str) -> tuple[Optional[str], Optional[str]]:
        """
        Usa IA para extraer nombre y resumen del perfil.

        Args:
            texto: Texto completo del CV.

        Returns:
            Tuple con (nombre, resumen) o (None, None) si falla.
        """
        # Si no hay analizador IA, intentar extracción básica con regex
        if not self.analizador_ia:
            logger.info("Sin analizador IA, usando extracción básica")
            nombre = self._extraer_nombre_basico(texto)
            resumen = self._generar_resumen_basico(texto)
            return nombre, resumen

        # Prompt para extraer información
        prompt = f"""
Analiza el siguiente CV y extrae SOLO esta información en formato JSON:

{{
  "nombre": "Nombre completo de la persona",
  "resumen": "Resumen profesional de 2 líneas máximo que describa: 
    - Años de experiencia
    - Rol principal 
    - Skills clave
    - Industria/sector"
}}

CV a analizar:
{texto[:3000]}  # Limitar a 3000 caracteres para no exceder token limit

Responde ÚNICAMENTE con el JSON, sin texto adicional.
"""

        try:
            # Usar el analizador IA para extraer información estructurada
            logger.info("Extrayendo con IA")
            respuesta = await self.analizador_ia.analizar(prompt)
            
            # Procesar la respuesta JSON
            import json
            datos = json.loads(respuesta)
            nombre = datos.get('nombre')
            resumen = datos.get('resumen')
            
            return nombre, resumen

        except Exception as e:
            logger.error(f"Error en extracción con IA: {e}")
            # Fallback a extracción básica
            return self._extraer_nombre_basico(texto), self._generar_resumen_basico(texto)

    def _extraer_nombre_basico(self, texto: str) -> Optional[str]:
        """
        Intenta extraer el nombre usando heurísticas básicas.

        Busca en las primeras líneas patrones comunes de nombres.

        Args:
            texto: Texto del CV.

        Returns:
            Nombre encontrado o None.
        """
        lineas = texto.split('\n')[:10]  # Buscar en las primeras 10 líneas

        for linea in lineas:
            linea = linea.strip()
            # Ignorar líneas muy cortas o muy largas
            if len(linea) < 5 or len(linea) > 60:
                continue

            # Ignorar líneas que parecen emails, teléfonos o títulos
            if '@' in linea or linea.isdigit() or linea.upper() == linea:
                continue

            # Podría ser un nombre (2-4 palabras, primera letra mayúscula)
            palabras = linea.split()
            if 2 <= len(palabras) <= 4:
                if all(p[0].isupper() for p in palabras if p):
                    return linea

        return None

    def _generar_resumen_basico(self, texto: str) -> str:
        """
        Genera un resumen básico usando las primeras líneas del CV.

        Args:
            texto: Texto del CV.

        Returns:
            Resumen de 2 líneas.
        """
        lineas = [l.strip() for l in texto.split('\n') if l.strip()]

        # Tomar las primeras 3-5 líneas no vacías
        resumen_lineas = lineas[:5]
        resumen = ' '.join(resumen_lineas)

        # Truncar a ~200 caracteres
        if len(resumen) > 200:
            resumen = resumen[:197] + "..."

        return resumen if resumen else "No se pudo generar resumen"

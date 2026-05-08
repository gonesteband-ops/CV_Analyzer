"""
Servicio de parsing de CVs.
Extrae texto de archivos PDF, DOCX y TXT.
"""
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)


class CVParserError(Exception):
    """Error al procesar un CV."""
    
    def __init__(self, mensaje: str, archivo: str, causa: Exception | None = None):
        super().__init__(mensaje)
        self.archivo = archivo
        self.causa = causa


class CVParser:
    """
    Servicio para extraer texto de CVs en diferentes formatos.
    
    Formatos soportados:
    - PDF (usando pdfplumber)
    - DOCX (usando python-docx)
    - TXT (lectura directa)
    """
    
    # Extensiones soportadas
    EXTENSIONES_SOPORTADAS = {'.pdf', '.docx', '.txt'}
    
    # Tamaño máximo: 10MB
    TAMANIO_MAXIMO = 10 * 1024 * 1024  # 10MB
    
    def __init__(self):
        """Inicializa el parser de CVs."""
        self._pdfplumber_disponible = None
        self._docx_disponible = None
    
    def _verificar_dependencias(self) -> None:
        """Verifica si las librerías de parsing están disponibles."""
        if self._pdfplumber_disponible is None:
            try:
                import pdfplumber
                self._pdfplumber_disponible = True
            except ImportError:
                self._pdfplumber_disponible = False
                logger.warning("pdfplumber no disponible. Parsing de PDF no funcionará.")
        
        if self._docx_disponible is None:
            try:
                from docx import Document
                self._docx_disponible = True
            except ImportError:
                self._docx_disponible = False
                logger.warning("python-docx no disponible. Parsing de DOCX no funcionará.")
    
    def extraer_texto(self, archivo_path: str | Path) -> Tuple[str, str]:
        """
        Extrae texto de un archivo CV.
        
        Args:
            archivo_path: Ruta al archivo del CV.
            
        Returns:
            Tuple[str, str]: (texto_extraido, tipo_archivo)
            
        Raises:
            CVParserError: Si el archivo no es válido o no se puede procesar.
        """
        archivo_path = Path(archivo_path)
        
        # Validar que el archivo existe
        if not archivo_path.exists():
            raise CVParserError(
                mensaje=f"El archivo no existe: {archivo_path.name}",
                archivo=archivo_path.name,
            )
        
        # Validar extensión
        extension = archivo_path.suffix.lower()
        if extension not in self.EXTENSIONES_SOPORTADAS:
            raise CVParserError(
                mensaje=f"Tipo de archivo no soportado: {extension}. Solo PDF, DOCX, TXT",
                archivo=archivo_path.name,
            )
        
        # Validar tamaño
        tamanio = archivo_path.stat().st_size
        if tamanio > self.TAMANIO_MAXIMO:
            raise CVParserError(
                mensaje=f"Archivo demasiado grande ({tamanio / 1024 / 1024:.2f}MB). Máximo 10MB",
                archivo=archivo_path.name,
            )
        
        # Verificar dependencias
        self._verificar_dependencias()
        
        # Extraer texto según el tipo
        try:
            if extension == '.pdf':
                return self._extraer_pdf(archivo_path), 'pdf'
            elif extension == '.docx':
                return self._extraer_docx(archivo_path), 'docx'
            elif extension == '.txt':
                return self._extraer_txt(archivo_path), 'txt'
            else:
                raise CVParserError(
                    mensaje=f"Tipo de archivo no soportado: {extension}",
                    archivo=archivo_path.name,
                )
        except CVParserError:
            raise
        except Exception as e:
            logger.error(f"Error al extraer texto de {archivo_path.name}: {e}")
            raise CVParserError(
                mensaje=f"Error al procesar el archivo: {str(e)}",
                archivo=archivo_path.name,
                causa=e,
            )
    
    def _extraer_pdf(self, archivo_path: Path) -> str:
        """
        Extrae texto de un archivo PDF usando pdfplumber.
        
        Args:
            archivo_path: Ruta al archivo PDF.
            
        Returns:
            str: Texto extraído del PDF.
            
        Raises:
            CVParserError: Si no se puede extraer el texto.
        """
        if not self._pdfplumber_disponible:
            raise CVParserError(
                mensaje="pdfplumber no está instalado. No se puede procesar PDF.",
                archivo=archivo_path.name,
            )
        
        try:
            import pdfplumber
            
            texto_completo = []
            
            with pdfplumber.open(archivo_path) as pdf:
                for pagina in pdf.pages:
                    texto_pagina = pagina.extract_text()
                    if texto_pagina:
                        texto_completo.append(texto_pagina)
            
            if not texto_completo:
                logger.warning(f"PDF {archivo_path.name} no tiene texto extraíble")
                return ""
            
            texto_resultante = "\n\n".join(texto_completo)
            logger.info(f"PDF {archivo_path.name} procesado: {len(texto_resultante)} caracteres")
            
            return texto_resultante
            
        except Exception as e:
            logger.error(f"Error al procesar PDF {archivo_path.name}: {e}")
            raise CVParserError(
                mensaje=f"Error al procesar PDF: {str(e)}",
                archivo=archivo_path.name,
                causa=e,
            )
    
    def _extraer_docx(self, archivo_path: Path) -> str:
        """
        Extrae texto de un archivo DOCX usando python-docx.
        
        Args:
            archivo_path: Ruta al archivo DOCX.
            
        Returns:
            str: Texto extraído del DOCX.
            
        Raises:
            CVParserError: Si no se puede extraer el texto.
        """
        if not self._docx_disponible:
            raise CVParserError(
                mensaje="python-docx no está instalado. No se puede procesar DOCX.",
                archivo=archivo_path.name,
            )
        
        try:
            from docx import Document
            
            doc = Document(archivo_path)
            
            # Extraer texto de párrafos
            parrafos = []
            for parrafo in doc.paragraphs:
                if parrafo.text.strip():
                    parrafos.append(parrafo.text)
            
            # Extraer texto de tablas (si las hay)
            for tabla in doc.tables:
                for fila in tabla.rows:
                    fila_texto = []
                    for celda in fila.cells:
                        if celda.text.strip():
                            fila_texto.append(celda.text)
                    if fila_texto:
                        parrafos.append(" | ".join(fila_texto))
            
            if not parrafos:
                logger.warning(f"DOCX {archivo_path.name} está vacío")
                return ""
            
            texto_resultante = "\n\n".join(parrafos)
            logger.info(f"DOCX {archivo_path.name} procesado: {len(texto_resultante)} caracteres")
            
            return texto_resultante
            
        except Exception as e:
            logger.error(f"Error al procesar DOCX {archivo_path.name}: {e}")
            raise CVParserError(
                mensaje=f"Error al procesar DOCX: {str(e)}",
                archivo=archivo_path.name,
                causa=e,
            )
    
    def _extraer_txt(self, archivo_path: Path) -> str:
        """
        Extrae texto de un archivo TXT (lectura directa).
        
        Args:
            archivo_path: Ruta al archivo TXT.
            
        Returns:
            str: Contenido del archivo TXT.
            
        Raises:
            CVParserError: Si no se puede leer el archivo.
        """
        try:
            # Intentar con diferentes encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with open(archivo_path, 'r', encoding=encoding) as f:
                        texto = f.read()
                        logger.info(f"TXT {archivo_path.name} procesado ({encoding}): {len(texto)} caracteres")
                        return texto
                except UnicodeDecodeError:
                    continue
            
            # Si ningún encoding funcionó
            raise CVParserError(
                mensaje="No se pudo decodificar el archivo TXT con ningún encoding soportado",
                archivo=archivo_path.name,
            )
            
        except Exception as e:
            if isinstance(e, CVParserError):
                raise
            logger.error(f"Error al procesar TXT {archivo_path.name}: {e}")
            raise CVParserError(
                mensaje=f"Error al leer archivo TXT: {str(e)}",
                archivo=archivo_path.name,
                causa=e,
            )
    
    def validar_archivo(self, archivo_path: str | Path) -> Tuple[bool, str]:
        """
        Valida si un archivo es un CV válido para procesamiento.
        
        Args:
            archivo_path: Ruta al archivo a validar.
            
        Returns:
            Tuple[bool, str]: (es_valido, mensaje_de_error)
        """
        archivo_path = Path(archivo_path)
        
        # Verificar existencia
        if not archivo_path.exists():
            return False, f"El archivo no existe: {archivo_path.name}"
        
        # Verificar extensión
        extension = archivo_path.suffix.lower()
        if extension not in self.EXTENSIONES_SOPORTADAS:
            return False, f"Tipo de archivo no soportado: {extension}"
        
        # Verificar tamaño
        tamanio = archivo_path.stat().st_size
        if tamanio > self.TAMANIO_MAXIMO:
            return False, f"Archivo demasiado grande ({tamanio / 1024 / 1024:.2f}MB). Máximo 10MB"
        
        if tamanio == 0:
            return False, "El archivo está vacío"
        
        return True, ""

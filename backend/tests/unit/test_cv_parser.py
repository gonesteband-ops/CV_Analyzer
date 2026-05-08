"""
Tests unitarios para el servicio CVParser.
Prueba extracción de texto de PDF, DOCX y TXT.
"""
import pytest
import tempfile
import os
from pathlib import Path

from services.cv_parser import CVParser, CVParserError


class TestCVParserValidacion:
    """Tests para validación de archivos."""

    def setup_method(self):
        """Configura el parser antes de cada test."""
        self.parser = CVParser()

    def test_validar_archivo_no_existe(self):
        """Debe retornar False para archivo que no existe."""
        es_valido, mensaje = self.parser.validar_archivo("archivo_inexistente.pdf")
        
        assert es_valido is False
        assert "no existe" in mensaje

    def test_validar_archivo_extension_no_soportada(self, tmp_path):
        """Debe retornar False para extensión no soportada."""
        archivo = tmp_path / "archivo.xls"
        archivo.write_text("contenido")
        
        es_valido, mensaje = self.parser.validar_archivo(archivo)
        
        assert es_valido is False
        assert "no soportado" in mensaje

    def test_validar_archivo_vacio(self, tmp_path):
        """Debe retornar False para archivo vacío."""
        archivo = tmp_path / "vacio.pdf"
        archivo.touch()  # Crea archivo vacío
        
        es_valido, mensaje = self.parser.validar_archivo(archivo)
        
        assert es_valido is False
        assert "vacío" in mensaje

    def test_validar_archivo_demasiado_grande(self, tmp_path):
        """Debe retornar False para archivo > 10MB."""
        archivo = tmp_path / "grande.pdf"
        
        # Crear archivo de 11MB (simulado)
        with open(archivo, 'wb') as f:
            f.write(b'x' * (11 * 1024 * 1024))
        
        es_valido, mensaje = self.parser.validar_archivo(archivo)
        
        assert es_valido is False
        assert "grande" in mensaje or "10MB" in mensaje

    def test_validar_archivo_valido(self, tmp_path):
        """Debe retornar True para archivo válido."""
        archivo = tmp_path / "valido.txt"
        archivo.write_text("contenido válido")
        
        es_valido, mensaje = self.parser.validar_archivo(archivo)
        
        assert es_valido is True
        assert mensaje == ""


class TestCVParserTXT:
    """Tests para extracción de texto de archivos TXT."""

    def setup_method(self):
        """Configura el parser antes de cada test."""
        self.parser = CVParser()

    def test_extraer_txt_utf8(self, tmp_path):
        """Debe extraer texto de archivo UTF-8."""
        contenido = "Nombre: Juan Pérez\nExperiencia: Ventas\nHabilidades: CRM, Negociación"
        archivo = tmp_path / "cv_utf8.txt"
        archivo.write_text(contenido, encoding='utf-8')
        
        texto, tipo = self.parser.extraer_texto(archivo)
        
        assert tipo == "txt"
        assert "Juan Pérez" in texto
        assert "Ventas" in texto
        assert "CRM" in texto

    def test_extraer_txt_latin1(self, tmp_path):
        """Debe extraer texto de archivo Latin-1."""
        contenido = "Nombre: María González\nExperiencia: Atención al cliente"
        archivo = tmp_path / "cv_latin1.txt"
        archivo.write_text(contenido, encoding='latin-1')
        
        texto, tipo = self.parser.extraer_texto(archivo)
        
        assert tipo == "txt"
        assert "María González" in texto

    def test_extraer_txt_no_existe(self):
        """Debe lanzar CVParserError para archivo inexistente."""
        with pytest.raises(CVParserError) as exc_info:
            self.parser.extraer_texto("archivo_no_existe.txt")
        
        assert "no existe" in str(exc_info.value)

    def test_extraer_txt_extension_invalida(self, tmp_path):
        """Debe lanzar CVParserError para extensión inválida."""
        archivo = tmp_path / "archivo.xls"
        archivo.write_text("contenido")
        
        with pytest.raises(CVParserError) as exc_info:
            self.parser.extraer_texto(archivo)
        
        assert "no soportado" in str(exc_info.value)


class TestCVParserPDF:
    """Tests para extracción de texto de archivos PDF."""

    def setup_method(self):
        """Configura el parser antes de cada test."""
        self.parser = CVParser()

    def test_extraer_pdf_no_existe(self):
        """Debe lanzar CVParserError para PDF inexistente."""
        with pytest.raises(CVParserError) as exc_info:
            self.parser.extraer_texto("archivo_no_existe.pdf")

        assert "no existe" in str(exc_info.value)

    def test_pdf_fallback_sin_pdfplumber(self, tmp_path):
        """Debe manejar gracefully si pdfplumber no está disponible."""
        # Crear archivo PDF falso (solo para testing de ruta de código)
        archivo = tmp_path / "falso.pdf"
        archivo.write_bytes(b'%PDF-1.4 contenido falso')

        # El parser debería intentar procesar y fallar o usar fallback
        # Este test verifica que no crashee
        try:
            texto, tipo = self.parser.extraer_texto(archivo)
            # Si funciona, verificar tipo
            assert tipo == "pdf"
        except CVParserError as e:
            # Si falla, debe ser error de procesamiento, no de validación
            assert "procesar" in str(e).lower() or "pdf" in str(e).lower()


class TestCVParserDOCX:
    """Tests para extracción de texto de archivos DOCX."""

    def setup_method(self):
        """Configura el parser antes de cada test."""
        self.parser = CVParser()

    def test_extraer_docx_no_existe(self):
        """Debe lanzar CVParserError para DOCX inexistente."""
        with pytest.raises(CVParserError) as exc_info:
            self.parser.extraer_texto("archivo_no_existe.docx")

        assert "no existe" in str(exc_info.value)

    def test_docx_fallback_sin_docx(self, tmp_path):
        """Debe manejar gracefully si python-docx no está disponible."""
        # Crear archivo DOCX falso
        archivo = tmp_path / "falso.docx"
        archivo.write_bytes(b'PK contenido falso')

        try:
            texto, tipo = self.parser.extraer_texto(archivo)
            assert tipo == "docx"
        except CVParserError as e:
            assert "procesar" in str(e).lower() or "docx" in str(e).lower()


class TestCVParserErrores:
    """Tests para manejo de errores del parser."""

    def test_cv_parser_error_con_causa(self):
        """CVParserError debe almacenar causa raíz."""
        causa = ValueError("error original")
        error = CVParserError(
            mensaje="Error al procesar",
            archivo="test.pdf",
            causa=causa
        )

        # CVParserError hereda de Exception, el mensaje es el primer arg
        assert "Error al procesar" in str(error)
        assert error.causa == causa

    def test_cv_parser_error_sin_causa(self):
        """CVParserError debe funcionar sin causa."""
        error = CVParserError(
            mensaje="Error simple",
            archivo="test.pdf"
        )

        assert "Error simple" in str(error)
        assert error.causa is None

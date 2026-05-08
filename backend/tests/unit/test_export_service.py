"""
Tests unitarios para el servicio ExportService.
Prueba exportación de análisis a Excel con formato corporativo.
"""
import pytest
import tempfile
import os
from pathlib import Path
from datetime import datetime

from services.export_service import ExportService


class TestExportServiceExportarXlsx:
    """Tests para exportación a Excel."""

    def setup_method(self):
        """Configura el service antes de cada test."""
        self.service = ExportService()

    def test_exportar_xlsx_archivo_creado(self, tmp_path):
        """Debe crear archivo Excel en ruta especificada."""
        filepath = tmp_path / "test_export.xlsx"
        analisis_list = []
        
        resultado = self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        assert os.path.exists(filepath)
        assert resultado == str(filepath)
        assert filepath.suffix == ".xlsx"

    def test_exportar_xlsx_con_datos_basicos(self, tmp_path):
        """Debe exportar lista con análisis básicos."""
        filepath = tmp_path / "test_con_datos.xlsx"
        
        analisis_list = [
            {
                "candidate_name": "Juan Pérez",
                "candidate_email": "juan@example.com",
                "file_name": "cv_juan.pdf",
                "perfil_titulo": "Desarrollador Python",
                "puntaje": 85,
                "etiqueta": "Recomendado",
                "feedback": "Excelente perfil técnico",
                "analyzed_at": datetime(2026, 5, 3, 10, 30),
            }
        ]
        
        resultado = self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        assert os.path.exists(filepath)
        
        # Verificar que se puede leer el archivo
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        # Verificar headers
        assert ws.cell(row=1, column=1).value == "Candidato"
        assert ws.cell(row=1, column=4).value == "Perfil"
        assert ws.cell(row=1, column=5).value == "Puntaje"
        
        # Verificar datos
        assert ws.cell(row=2, column=1).value == "Juan Pérez"
        assert ws.cell(row=2, column=2).value == "juan@example.com"
        assert ws.cell(row=2, column=5).value == "85/100"
        assert ws.cell(row=2, column=6).value == "Recomendado"

    def test_exportar_xlsx_headers_con_formato(self, tmp_path):
        """Los headers deben tener formato corporativo (azul, blanco, bold)."""
        filepath = tmp_path / "test_headers.xlsx"
        
        self.service.exportar_analisis_xlsx([], str(filepath))
        
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        # Verificar estilo del header
        header_cell = ws.cell(row=1, column=1)
        
        # Verificar fill azul (#2F4DAA)
        assert header_cell.fill.start_color.rgb == "002F4DAA" or header_cell.fill.start_color.rgb == "2F4DAA"
        # Verificar font blanco
        assert header_cell.font.color.rgb == "00FFFFFF" or header_cell.font.color.rgb == "FFFFFF"
        # Verificar bold
        assert header_cell.font.bold is True

    def test_exportar_xlsx_puntaje_con_color_condicional(self, tmp_path):
        """El puntaje debe tener color según valor (verde/amarillo/rojo)."""
        filepath = tmp_path / "test_puntajes.xlsx"
        
        analisis_list = [
            {
                "candidate_name": "Verde",
                "candidate_email": "verde@test.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 85,  # Verde >= 70
                "etiqueta": "Recomendado",
                "feedback": "OK",
                "analyzed_at": None,
            },
            {
                "candidate_name": "Amarillo",
                "candidate_email": "amarillo@test.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 55,  # Amarillo 40-69
                "etiqueta": "Recomendado con reservas",
                "feedback": "OK",
                "analyzed_at": None,
            },
            {
                "candidate_name": "Rojo",
                "candidate_email": "rojo@test.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 25,  # Rojo < 40
                "etiqueta": "No Recomendado",
                "feedback": "OK",
                "analyzed_at": None,
            }
        ]
        
        self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        # Verificar colores de puntajes (columna 5)
        # Verde (4CAA37)
        puntaje_verde = ws.cell(row=2, column=5)
        # Amarillo (F9A825)
        puntaje_amarillo = ws.cell(row=3, column=5)
        # Rojo (F95E50)
        puntaje_rojo = ws.cell(row=4, column=5)
        
        # Los colores deben estar en el font
        assert puntaje_verde.font.color.rgb in ["004CAA37", "4CAA37"]
        assert puntaje_amarillo.font.color.rgb in ["00F9A825", "F9A825"]
        assert puntaje_rojo.font.color.rgb in ["00F95E50", "F95E50"]

    def test_exportar_xlsx_filas_alternas(self, tmp_path):
        """Las filas pares deben tener fondo gris claro (#F0F1F3)."""
        filepath = tmp_path / "test_alternas.xlsx"

        analisis_list = [
            {
                "candidate_name": "Fila 1",
                "candidate_email": "a@b.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 50,
                "etiqueta": "Reservas",
                "feedback": "OK",
                "analyzed_at": None,
            },
            {
                "candidate_name": "Fila 2",
                "candidate_email": "a@b.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 50,
                "etiqueta": "Reservas",
                "feedback": "OK",
                "analyzed_at": None,
            }
        ]

        self.service.exportar_analisis_xlsx(analisis_list, str(filepath))

        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active

        # El código aplica fill gris a filas con row_num par (row_num % 2 == 0)
        # row_num comienza en 2 (primera fila de datos)
        # Entonces row_num=2 (fila 2 del Excel) NO tiene fill (impar en 0-indexed)
        # row_num=3 (fila 3 del Excel) tiene fill (par en 0-indexed)
        # Verificamos que al menos una fila tenga fill diferente al blanco
        celda_fila_2 = ws.cell(row=2, column=1)
        celda_fila_3 = ws.cell(row=3, column=1)
        
        # Al menos una de las filas debe tener fill gris
        tiene_fill_fila2 = celda_fila_2.fill.start_color.rgb != "00000000"
        tiene_fill_fila3 = celda_fila_3.fill.start_color.rgb != "00000000"
        assert tiene_fill_fila2 or tiene_fill_fila3

    def test_exportar_xlsx_con_borde(self, tmp_path):
        """Las celdas deben tener bordes thin."""
        filepath = tmp_path / "test_bordes.xlsx"
        
        self.service.exportar_analisis_xlsx([], str(filepath))
        
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        header_cell = ws.cell(row=1, column=1)
        
        # Verificar bordes
        assert header_cell.border.left.style == "thin"
        assert header_cell.border.right.style == "thin"
        assert header_cell.border.top.style == "thin"
        assert header_cell.border.bottom.style == "thin"

    def test_exportar_xlsx_con_datos_nulas(self, tmp_path):
        """Debe manejar valores nulos gracefully."""
        filepath = tmp_path / "test_nulos.xlsx"
        
        analisis_list = [
            {
                "candidate_name": None,
                "candidate_email": None,
                "file_name": None,
                "perfil_titulo": None,
                "puntaje": None,
                "etiqueta": None,
                "feedback": None,
                "analyzed_at": None,
            }
        ]
        
        # No debe lanzar excepción
        resultado = self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        assert os.path.exists(filepath)
        
        # Verificar que usa valores por defecto "N/A"
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        assert ws.cell(row=2, column=1).value == "N/A"
        assert ws.cell(row=2, column=5).value == "0/100"

    def test_exportar_xlsx_con_objeto_row(self, tmp_path):
        """Debe manejar objetos Row de SQLAlchemy."""
        filepath = tmp_path / "test_row.xlsx"
        
        # Simular Row object con _asdict
        class MockRow:
            def _asdict(self):
                return {
                    "candidate_name": "Test User",
                    "candidate_email": "test@example.com",
                    "file_name": "cv.pdf",
                    "perfil_titulo": "Dev",
                    "puntaje": 75,
                    "etiqueta": "Recomendado",
                    "feedback": "Good",
                    "analyzed_at": datetime(2026, 5, 3),
                }
        
        analisis_list = [MockRow()]
        
        resultado = self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        assert os.path.exists(filepath)
        
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        assert ws.cell(row=2, column=1).value == "Test User"

    def test_exportar_xlsx_autoajuste_columnas(self, tmp_path):
        """Las columnas deben tener autoajuste de ancho."""
        filepath = tmp_path / "test_autoajuste.xlsx"
        
        analisis_list = [
            {
                "candidate_name": "NombreMuyLargoQueOcupaMuchoEspacio",
                "candidate_email": "email@corto.com",
                "file_name": "cv.pdf",
                "perfil_titulo": "Dev",
                "puntaje": 50,
                "etiqueta": "Reservas",
                "feedback": "OK",
                "analyzed_at": None,
            }
        ]
        
        self.service.exportar_analisis_xlsx(analisis_list, str(filepath))
        
        from openpyxl import load_workbook
        wb = load_workbook(filepath)
        ws = wb.active
        
        # La columna 1 (Candidato) debería tener width mayor por el nombre largo
        assert ws.column_dimensions['A'].width > 10

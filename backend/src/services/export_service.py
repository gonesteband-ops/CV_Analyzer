from datetime import datetime
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)


class ExportService:
    """
    Servicio para exportar análisis de CVs a archivos Excel (.xlsx).
    Aplica formato corporativo: colores, bordes, autoajuste y condicionales.
    """

    def exportar_analisis_xlsx(self, analisis_list: list, filepath: str) -> str:
        """
        Exporta una lista de análisis a un archivo Excel con formato corporativo.

        Args:
            analisis_list: Lista de objetos Row de SQLAlchemy con campos:
                - cv_id, candidate_name, candidate_email, file_name
                - perfil_titulo, puntaje, etiqueta, feedback
                - fortalezas, debilidades, analyzed_at
            filepath: Ruta completa donde guardar el archivo .xlsx

        Returns:
            str: Ruta del archivo generado

        Raises:
            Exception: Si ocurre un error durante la generación del archivo
        """
        try:
            # Crear libro de trabajo y hoja
            wb = Workbook()
            ws = wb.active
            ws.title = "Analisis"

            # Headers
            headers = [
                "Candidato",
                "Email",
                "Archivo",
                "Perfil",
                "Puntaje",
                "Etiqueta",
                "Feedback",
                "Fecha",
            ]

            # Estilos
            header_font = Font(color="FFFFFF", bold=True)
            header_fill = PatternFill(start_color="2F4DAA", end_color="2F4DAA", fill_type="solid")
            border = Border(
                left=Side(style="thin"),
                right=Side(style="thin"),
                top=Side(style="thin"),
                bottom=Side(style="thin"),
            )
            alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)

            # Escribir headers
            for col_num, header in enumerate(headers, 1):
                cell = ws.cell(row=1, column=col_num, value=header)
                cell.font = header_font
                cell.fill = header_fill
                cell.border = border
                cell.alignment = alignment

            # Escribir datos
            for row_num, analisis in enumerate(analisis_list, 2):
                # Convertir Row a diccionario si es necesario
                if hasattr(analisis, '_asdict'):
                    analisis_dict = analisis._asdict()
                elif isinstance(analisis, dict):
                    analisis_dict = analisis
                else:
                    analisis_dict = {
                        "candidate_name": getattr(analisis, "candidate_name", "N/A"),
                        "candidate_email": getattr(analisis, "candidate_email", "N/A"),
                        "file_name": getattr(analisis, "file_name", "N/A"),
                        "perfil_titulo": getattr(analisis, "perfil_titulo", "N/A"),
                        "puntaje": getattr(analisis, "puntaje", 0),
                        "etiqueta": getattr(analisis, "etiqueta", "N/A"),
                        "feedback": getattr(analisis, "feedback", "Sin feedback"),
                        "analyzed_at": getattr(analisis, "analyzed_at", None),
                    }

                # Formatear fecha
                fecha_str = "N/A"
                if analisis_dict.get("analyzed_at"):
                    try:
                        dt = analisis_dict["analyzed_at"]
                        if isinstance(dt, str):
                            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
                        fecha_str = dt.strftime("%d/%m/%Y %H:%M")
                    except Exception as e:
                        logger.warning(f"Error al formatear fecha {analisis_dict.get('analyzed_at')}: {e}")
                        fecha_str = "Fecha inválida"

                # Determinar color del puntaje
                puntaje = analisis_dict.get("puntaje") or 0
                if puntaje >= 70:
                    score_color = "4CAA37"
                elif puntaje >= 40:
                    score_color = "F9A825"
                else:
                    score_color = "F95E50"

                # Datos de fila
                row_data = [
                    str(analisis_dict.get("candidate_name") or "N/A"),
                    str(analisis_dict.get("candidate_email") or "N/A"),
                    str(analisis_dict.get("file_name") or "N/A"),
                    str(analisis_dict.get("perfil_titulo") or "N/A"),
                    f"{puntaje}/100",
                    str(analisis_dict.get("etiqueta") or "N/A"),
                    str(analisis_dict.get("feedback") or "Sin feedback"),
                    fecha_str,
                ]

                # Escribir fila
                for col_num, value in enumerate(row_data, 1):
                    cell = ws.cell(row=row_num, column=col_num, value=value)
                    cell.border = border
                    cell.alignment = alignment

                    # Aplicar color condicional solo al puntaje (columna 5)
                    if col_num == 5:
                        cell.font = Font(color=score_color, bold=True)

                # Aplicar fondo alternado (gris claro para filas pares)
                if row_num % 2 == 0:
                    for col_num in range(1, len(headers) + 1):
                        cell = ws.cell(row=row_num, column=col_num)
                        cell.fill = PatternFill(start_color="F0F1F3", end_color="F0F1F3", fill_type="solid")

            # Autoajustar columnas
            for column_cells in ws.columns:
                length = max(len(str(cell.value)) for cell in column_cells)
                ws.column_dimensions[get_column_letter(column_cells[0].column)].width = min(length + 2, 50)

            # Guardar archivo
            wb.save(filepath)
            logger.info(f"Archivo Excel exportado exitosamente: {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Error al exportar análisis a Excel: {e}", exc_info=True)
            raise e
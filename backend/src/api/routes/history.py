from datetime import datetime
import logging
import os
import tempfile
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.responses import FileResponse
from sqlalchemy.orm import Session

from api.deps import get_db, require_auth
from models.analisis import Analisis
from models.cv import CV
from models.perfil_cargo import PerfilCargo
from models.usuario import Usuario
from services.export_service import ExportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/history", tags=["History"])

# Templates
templates = Jinja2Templates(directory="templates")


@router.get("")
def get_history(
    perfil_id: Optional[int] = Query(None, description="ID del perfil de cargo"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (formato ISO: YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (formato ISO: YYYY-MM-DD)"),
    puntaje_min: Optional[int] = Query(None, ge=0, le=100, description="Puntaje mínimo (0-100)"),
    puntaje_max: Optional[int] = Query(None, ge=0, le=100, description="Puntaje máximo (0-100)"),
    etiqueta: Optional[str] = Query(None, description="Etiqueta: 'Recomendado', 'Recomendado con reservas', 'No Recomendado'"),
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre del candidato"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Obtiene el histórico de análisis con filtros avanzados y paginación.

    - Filtra por perfil de cargo, rango de fechas, puntaje, etiqueta y búsqueda por nombre.
    - Aplica joins con CV y PerfilCargo para obtener datos relacionados.
    - Retorna resultados paginados en formato JSON.
    """
    try:
        # Construir la query base con joins
        query = db.query(
            Analisis.id.label("analisis_id"),
            Analisis.puntaje,
            Analisis.etiqueta,
            Analisis.feedback,
            Analisis.fortalezas,
            Analisis.debilidades,
            Analisis.analyzed_at,
            CV.id.label("cv_id"),
            CV.candidate_name,
            CV.candidate_email,
            CV.file_name,
            PerfilCargo.titulo.label("perfil_titulo"),
        ).join(CV, Analisis.cv_id == CV.id).join(
            PerfilCargo, Analisis.perfil_id == PerfilCargo.id
        )

        # Aplicar filtros condicionales
        if perfil_id is not None:
            query = query.filter(Analisis.perfil_id == perfil_id)

        if fecha_desde:
            try:
                dt_desde = datetime.fromisoformat(fecha_desde + "T00:00:00")
                query = query.filter(Analisis.analyzed_at >= dt_desde)
            except ValueError as e:
                logger.warning(f"Formato inválido para fecha_desde '{fecha_desde}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha_desde inválido. Use YYYY-MM-DD",
                )

        if fecha_hasta:
            try:
                dt_hasta = datetime.fromisoformat(fecha_hasta + "T23:59:59")
                query = query.filter(Analisis.analyzed_at <= dt_hasta)
            except ValueError as e:
                logger.warning(f"Formato inválido para fecha_hasta '{fecha_hasta}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha_hasta inválido. Use YYYY-MM-DD",
                )

        if puntaje_min is not None:
            query = query.filter(Analisis.puntaje >= puntaje_min)

        if puntaje_max is not None:
            query = query.filter(Analisis.puntaje <= puntaje_max)

        if etiqueta:
            query = query.filter(Analisis.etiqueta == etiqueta)

        if busqueda:
            query = query.filter(CV.candidate_name.ilike(f"%{busqueda}%"))

        # Contar total antes de aplicar paginación
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        # Convertir resultados a lista de diccionarios
        results_list = []
        for r in results:
            results_list.append({
                "cv_id": r.cv_id,
                "candidate_name": r.candidate_name or "N/A",
                "candidate_email": r.candidate_email or "N/A",
                "file_name": r.file_name or "N/A",
                "perfil_titulo": r.perfil_titulo or "N/A",
                "puntaje": r.puntaje,
                "etiqueta": r.etiqueta or "N/A",
                "feedback": r.feedback or "Sin feedback",
                "fortalezas": r.fortalezas or [],
                "debilidades": r.debilidades or [],
                "analyzed_at": r.analyzed_at.isoformat() if r.analyzed_at else None,
            })

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "results": results_list,
        }

    except HTTPException:
        raise  # Re-lanzar excepciones HTTP directas
    except Exception as e:
        logger.error(f"Error al obtener histórico de análisis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al procesar la solicitud",
        )


@router.get("/export")
def export_history(
    perfil_id: Optional[int] = Query(None, description="ID del perfil de cargo"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (formato ISO: YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (formato ISO: YYYY-MM-DD)"),
    puntaje_min: Optional[int] = Query(None, ge=0, le=100, description="Puntaje mínimo (0-100)"),
    puntaje_max: Optional[int] = Query(None, ge=0, le=100, description="Puntaje máximo (0-100)"),
    etiqueta: Optional[str] = Query(None, description="Etiqueta: 'Recomendado', 'Recomendado con reservas', 'No Recomendado'"),
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre del candidato"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Exporta el histórico de análisis filtrado a un archivo Excel (.xlsx).

    - Aplica los mismos filtros que GET /api/history.
    - Genera un archivo XLSX con formato corporativo usando ExportService.
    - Retorna el archivo como descarga.
    """
    try:
        # Construir la query base con joins (igual que en get_history)
        query = db.query(
            Analisis.id.label("analisis_id"),
            Analisis.puntaje,
            Analisis.etiqueta,
            Analisis.feedback,
            Analisis.fortalezas,
            Analisis.debilidades,
            Analisis.analyzed_at,
            CV.id.label("cv_id"),
            CV.candidate_name,
            CV.candidate_email,
            CV.file_name,
            PerfilCargo.titulo.label("perfil_titulo"),
        ).join(CV, Analisis.cv_id == CV.id).join(
            PerfilCargo, Analisis.perfil_id == PerfilCargo.id
        )

        # Aplicar filtros condicionales (igual que en get_history)
        if perfil_id is not None:
            query = query.filter(Analisis.perfil_id == perfil_id)

        if fecha_desde:
            try:
                dt_desde = datetime.fromisoformat(fecha_desde + "T00:00:00")
                query = query.filter(Analisis.analyzed_at >= dt_desde)
            except ValueError as e:
                logger.warning(f"Formato inválido para fecha_desde '{fecha_desde}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha_desde inválido. Use YYYY-MM-DD",
                )

        if fecha_hasta:
            try:
                dt_hasta = datetime.fromisoformat(fecha_hasta + "T23:59:59")
                query = query.filter(Analisis.analyzed_at <= dt_hasta)
            except ValueError as e:
                logger.warning(f"Formato inválido para fecha_hasta '{fecha_hasta}': {e}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Formato de fecha_hasta inválido. Use YYYY-MM-DD",
                )

        if puntaje_min is not None:
            query = query.filter(Analisis.puntaje >= puntaje_min)

        if puntaje_max is not None:
            query = query.filter(Analisis.puntaje <= puntaje_max)

        if etiqueta:
            query = query.filter(Analisis.etiqueta == etiqueta)

        if busqueda:
            query = query.filter(CV.candidate_name.ilike(f"%{busqueda}%"))

        # Obtener todos los resultados (sin paginación)
        results = query.all()

        # Crear archivo temporal
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, f"analisis_historico_{usuario.id}_{int(datetime.now().timestamp())}.xlsx")

        # Exportar
        export_service = ExportService()
        export_service.exportar_analisis_xlsx(results, filepath)

        # Retornar como FileResponse
        return FileResponse(
            path=filepath,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename="analisis_historico.xlsx",
        )

    except HTTPException:
        raise  # Re-lanzar excepciones HTTP directas
    except Exception as e:
        logger.error(f"Error al exportar histórico de análisis: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al generar el archivo Excel",
        )


def _build_history_query(db: Session, perfil_id: Optional[int] = None, fecha_desde: Optional[str] = None,
                          fecha_hasta: Optional[str] = None, puntaje_min: Optional[int] = None,
                          puntaje_max: Optional[int] = None, etiqueta: Optional[str] = None,
                          busqueda: Optional[str] = None):
    """
    Construye la query base con filtros para el histórico.
    """
    query = db.query(
        Analisis.id.label("analisis_id"),
        Analisis.puntaje,
        Analisis.etiqueta,
        Analisis.feedback,
        Analisis.fortalezas,
        Analisis.debilidades,
        Analisis.analyzed_at,
        CV.id.label("cv_id"),
        CV.candidate_name,
        CV.candidate_email,
        CV.file_name,
        PerfilCargo.titulo.label("perfil_titulo"),
    ).join(CV, Analisis.cv_id == CV.id).join(
        PerfilCargo, Analisis.perfil_id == PerfilCargo.id
    )

    if perfil_id is not None:
        query = query.filter(Analisis.perfil_id == perfil_id)

    if fecha_desde:
        try:
            dt_desde = datetime.fromisoformat(fecha_desde + "T00:00:00")
            query = query.filter(Analisis.analyzed_at >= dt_desde)
        except ValueError:
            pass

    if fecha_hasta:
        try:
            dt_hasta = datetime.fromisoformat(fecha_hasta + "T23:59:59")
            query = query.filter(Analisis.analyzed_at <= dt_hasta)
        except ValueError:
            pass

    if puntaje_min is not None:
        query = query.filter(Analisis.puntaje >= puntaje_min)

    if puntaje_max is not None:
        query = query.filter(Analisis.puntaje <= puntaje_max)

    if etiqueta:
        query = query.filter(Analisis.etiqueta == etiqueta)

    if busqueda:
        query = query.filter(CV.candidate_name.ilike(f"%{busqueda}%"))

    return query


@router.get("/table-html", response_class=HTMLResponse)
def get_history_table_html(
    request: Request,
    perfil_id: Optional[int] = Query(None, description="ID del perfil de cargo"),
    fecha_desde: Optional[str] = Query(None, description="Fecha desde (formato ISO: YYYY-MM-DD)"),
    fecha_hasta: Optional[str] = Query(None, description="Fecha hasta (formato ISO: YYYY-MM-DD)"),
    puntaje_min: Optional[int] = Query(None, ge=0, le=100, description="Puntaje mínimo (0-100)"),
    puntaje_max: Optional[int] = Query(None, ge=0, le=100, description="Puntaje máximo (0-100)"),
    etiqueta: Optional[str] = Query(None, description="Etiqueta"),
    busqueda: Optional[str] = Query(None, description="Búsqueda por nombre del candidato"),
    page: int = Query(1, ge=1, description="Número de página"),
    page_size: int = Query(20, ge=1, le=100, description="Elementos por página"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Retorna el HTML de la tabla de histórico para HTMX.
    """
    try:
        # Construir query con filtros
        query = _build_history_query(
            db, perfil_id, fecha_desde, fecha_hasta, puntaje_min, puntaje_max, etiqueta, busqueda
        )

        # Contar total
        total = query.count()

        # Aplicar paginación
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()

        # Calcular total de páginas
        total_pages = (total + page_size - 1) // page_size if total > 0 else 1

        # Generar HTML de la tabla
        if not results:
            return '''
<div class="text-center py-12 text-gray-500">
    <p class="text-lg">No se encontraron análisis</p>
    <p class="text-sm mt-2">Intenta ajustar los filtros de búsqueda</p>
</div>
'''

        # Construir filas de la tabla
        rows_html = ""
        for r in results:
            # Color del puntaje
            if r.puntaje >= 70:
                score_class = "text-success-600 bg-success-50"
                score_label = "Recomendado"
            elif r.puntaje >= 40:
                score_class = "text-yellow-700 bg-yellow-50"
                score_label = "Con reservas"
            else:
                score_class = "text-danger-600 bg-danger-50"
                score_label = "No recomendado"

            fecha_str = "N/A"
            if r.analyzed_at:
                try:
                    fecha_str = r.analyzed_at.strftime("%d/%m/%Y %H:%M")
                except Exception:
                    fecha_str = "Fecha inválida"

            rows_html += f'''
<tr class="border-b border-gray-100 hover:bg-gray-50">
    <td class="py-3 px-4">{r.candidate_name or 'N/A'}</td>
    <td class="py-3 px-4 text-gray-600">{r.candidate_email or 'N/A'}</td>
    <td class="py-3 px-4 text-gray-600">{r.file_name or 'N/A'}</td>
    <td class="py-3 px-4">{r.perfil_titulo or 'N/A'}</td>
    <td class="py-3 px-4">
        <span class="inline-flex items-center px-3 py-1 rounded-full text-xs font-medium {score_class}">
            {r.puntaje}/100 - {score_label}
        </span>
    </td>
    <td class="py-3 px-4 text-sm text-gray-600">{fecha_str}</td>
</tr>
'''

        # Construir paginación
        pagination_html = ""
        if total_pages > 1:
            pagination_items = []
            for p in range(1, total_pages + 1):
                if p == page:
                    pagination_items.append(f'<span class="px-3 py-1 rounded bg-[#2F4DAA] text-white">{p}</span>')
                else:
                    pagination_items.append(f'<a href="#" class="px-3 py-1 rounded hover:bg-gray-200" hx-get="/api/history/table-html?page={p}&perfil_id={perfil_id or ""}&fecha_desde={fecha_desde or ""}&fecha_hasta={fecha_hasta or ""}&puntaje_min={puntaje_min or ""}&puntaje_max={puntaje_max or ""}&etiqueta={etiqueta or ""}&busqueda={busqueda or ""}&page_size={page_size}" hx-target="#history-table-container" hx-swap="innerHTML">{p}</a>')
            
            pagination_html = f'''
<div class="flex justify-center items-center gap-2 mt-6">
    <span class="text-sm text-gray-600">Página {page} de {total_pages}</span>
    <div class="flex gap-1">{" ".join(pagination_items)}</div>
</div>
'''

        html = f'''
<div class="overflow-x-auto">
    <table class="min-w-full bg-white rounded-lg overflow-hidden">
        <thead class="bg-[#2F4DAA] text-white">
            <tr>
                <th class="py-3 px-4 text-left text-sm font-semibold">Candidato</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Email</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Archivo</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Perfil</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Puntaje</th>
                <th class="py-3 px-4 text-left text-sm font-semibold">Fecha</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
    {pagination_html}
</div>
<div class="text-sm text-gray-600 mt-4 text-center">
    Mostrando {len(results)} de {total} análisis
</div>
'''
        return html

    except Exception as e:
        logger.error(f"Error al generar tabla de histórico: {e}", exc_info=True)
        return HTMLResponse(
            content='<div class="text-center py-12 text-danger-600"><p>Error al cargar la tabla</p></div>',
            status_code=500,
        )


@router.get("/page")
def get_history_page(
    request: Request,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Página principal del histórico con filtros.
    """
    return templates.TemplateResponse(
        "pages/historico.html",
        {"request": request, "usuario": usuario},
    )
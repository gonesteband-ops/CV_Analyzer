"""
Rutas de API para gestion de CVs.
"""
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List
import json

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import JSONResponse
from starlette.responses import HTMLResponse
from sqlalchemy.orm import Session

from api.deps import get_db, require_auth
from core.config import settings
from models.cv import CV
from models.upload_batch import UploadBatch
from models.analisis import Analisis
from models.schemas_cv import (
    CVFileUploadResponse,
    CVUploadResponse,
    CVUploadStatusResponse,
    CVResponse,
    CVAnalysisResponse,
    BatchAnalysisRequest,
    BatchAnalysisStatusResponse,
)
from models.usuario import Usuario
from services.cv_parser import CVParser, CVParserError
from services.cv_extractor import ExtractorCV, InformacionCV
from services.matching import MatchingService
from services.ia_analyzer.groq import GroqAdapter
from services.ia_analyzer.local import LocalAdapter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/cvs", tags=["CVs"])

# Directorio de uploads (en la raiz del proyecto)
CURRENT_DIR = Path(__file__).resolve().parent  # backend/src/api/routes
PROJECT_ROOT = CURRENT_DIR.parent.parent.parent  # analizer_beta_2
UPLOAD_DIR = PROJECT_ROOT / "uploads"


@router.post("/upload-cv")
async def upload_cv_batch(
    files: list[UploadFile] = File(..., description="Archivos CV en formato PDF (maximo 50)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    if len(files) > settings.max_files_per_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demasiados archivos ({len(files)}). Maximo {settings.max_files_per_batch} por lote",
        )

    resultados: list[dict] = []

    for file in files:
        try:
            file_ext = Path(file.filename or "").suffix.lower()
            if file_ext != ".pdf":
                resultados.append({
                    "success": False,
                    "file_name": file.filename,
                    "error": f"Tipo de archivo no soportado: {file_ext}. Solo PDF",
                })
                continue

            content = await file.read()
            size = len(content)

            if size > settings.max_file_size_bytes:
                resultados.append({
                    "success": False,
                    "file_name": file.filename,
                    "error": f"Archivo demasiado grande ({size / 1024 / 1024:.2f}MB). Maximo {settings.max_file_size_mb}MB",
                })
                continue

            if size == 0:
                resultados.append({
                    "success": False,
                    "file_name": file.filename,
                    "error": "El archivo esta vacio",
                })
                continue

            await file.seek(0)

            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename

            with open(file_path, "wb") as f:
                f.write(content)

            extractor = ExtractorCV()
            informacion: InformacionCV = extractor.extraer_informacion_sync(str(file_path))

            cv = CV(
                file_name=file.filename or "unknown",
                file_type=file_ext[1:],
                file_size=size,
                uploaded_by=usuario.id,
                status="processed",
                uploaded_at=datetime.utcnow(),
                extracted_text=informacion.texto_completo,
                candidate_name=informacion.nombre,
                candidate_email=informacion.email,
                candidate_phone=informacion.telefono,
                candidate_summary=informacion.resumen,
            )
            db.add(cv)
            db.commit()
            db.refresh(cv)

            logger.info(f"CV subido y procesado: {file.filename} (id={cv.id}, usuario={usuario.id})")

            resultados.append({
                "success": True,
                "cv_id": cv.id,
                "file_name": file.filename,
                "extracted_data": {
                    "nombre": informacion.nombre,
                    "email": informacion.email,
                    "telefono": informacion.telefono,
                    "resumen": informacion.resumen,
                },
            })

        except Exception as e:
            logger.error(f"Error al subir y procesar CV {file.filename}: {e}", exc_info=True)
            db.rollback()
            resultados.append({
                "success": False,
                "file_name": file.filename,
                "error": f"Error al procesar: {str(e)}",
            })

    return {
        "success": True,
        "total_files": len(files),
        "processed": sum(1 for r in resultados if r.get("success")),
        "failed": sum(1 for r in resultados if not r.get("success")),
        "results": resultados,
    }


async def _validar_archivo(file: UploadFile, max_size: int, allowed_extensions: list[str]) -> tuple[bool, str]:
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext not in allowed_extensions:
        return False, f"Tipo de archivo no soportado: {file_ext}. Solo {', '.join(allowed_extensions)}"

    size = getattr(file, "size", None)
    if size is None:
        contenido = await file.read()
        size = len(contenido)
        await file.seek(0)

    if size > max_size:
        return False, f"Archivo demasiado grande ({size / 1024 / 1024:.2f}MB). Maximo {max_size / 1024 / 1024:.0f}MB"

    if size == 0:
        return False, "El archivo esta vacio"

    return True, ""


@router.post("/upload", response_model=CVUploadResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_cvs(
    request: Request,
    files: List[UploadFile] = File(..., description="Archivos CV a subir (PDF, DOCX, TXT)"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    if len(files) > settings.max_files_per_batch:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Demasiados archivos ({len(files)}). Maximo {settings.max_files_per_batch} por lote",
        )

    errores_validacion = []
    archivos_validos = []

    for file in files:
        es_valido, mensaje_error = await _validar_archivo(
            file, settings.max_file_size_bytes, settings.allowed_extensions,
        )

        if not es_valido:
            errores_validacion.append(f"{file.filename}: {mensaje_error}")
        else:
            archivos_validos.append(file)

    if errores_validacion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Errores de validacion en algunos archivos", "errors": errores_validacion},
        )

    upload_id = str(uuid.uuid4())

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    upload_batch = UploadBatch(
        upload_id=upload_id,
        status="uploaded",
        total_files=len(archivos_validos),
        processed_files=0,
        created_by=usuario.id,
    )
    db.add(upload_batch)
    db.commit()
    db.refresh(upload_batch)

    cvs_subidos: list[CVFileUploadResponse] = []

    for file in archivos_validos:
        try:
            content = await file.read()

            file_ext = Path(file.filename or "").suffix.lower()
            unique_filename = f"{uuid.uuid4()}{file_ext}"
            file_path = UPLOAD_DIR / unique_filename

            with open(file_path, "wb") as f:
                f.write(content)

            extractor = ExtractorCV()
            informacion: InformacionCV = extractor.extraer_informacion_sync(str(file_path))

            cv = CV(
                file_name=file.filename or "unknown",
                file_type=file_ext[1:],
                file_size=len(content),
                uploaded_by=usuario.id,
                upload_batch_id=upload_batch.id,
                status="processed",
                uploaded_at=datetime.utcnow(),
                extracted_text=informacion.texto_completo,
                candidate_name=informacion.nombre,
                candidate_email=informacion.email,
                candidate_phone=informacion.telefono,
                candidate_summary=informacion.resumen,
            )
            db.add(cv)
            db.commit()
            db.refresh(cv)

            upload_batch.processed_files += 1
            db.commit()

            cvs_subidos.append(CVFileUploadResponse(
                file_name=file.filename or "unknown",
                file_id=cv.id,
                status="processed",
                file_type=file_ext[1:],
                file_size=len(content),
            ))

            logger.info(f"CV subido y procesado: {file.filename} (id={cv.id}, upload_id={upload_id})")

        except Exception as e:
            logger.error(f"Error al subir y procesar archivo {file.filename}: {e}", exc_info=True)
            db.rollback()
            cvs_subidos.append(CVFileUploadResponse(
                file_name=file.filename or "unknown",
                file_id=-1,
                status="error",
                file_type=Path(file.filename or "").suffix.lower()[1:],
                file_size=0,
            ))

    upload_batch.status = "completed"
    db.commit()

    logger.info(f"Upload batch {upload_id}: {len(cvs_subidos)} archivos procesados exitosamente")

    return CVUploadResponse(
        upload_id=upload_id,
        status="completed",
        files=cvs_subidos,
        message=f"{len(cvs_subidos)} archivos procesados exitosamente.",
    )


@router.get("/upload-status/{upload_id}", response_model=CVUploadStatusResponse)
async def get_upload_status(
    upload_id: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    upload_batch = db.query(UploadBatch).filter(
        UploadBatch.upload_id == upload_id,
        UploadBatch.created_by == usuario.id,
    ).first()

    if not upload_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el upload batch con id {upload_id}",
        )

    cvs = db.query(CV).filter(
        CV.upload_batch_id == upload_batch.id,
    ).all()

    files_status = [
        CVFileUploadResponse(
            file_name=cv.file_name,
            file_id=cv.id,
            status=cv.status,
            file_type=cv.file_type,
            file_size=cv.file_size,
        )
        for cv in cvs
    ]

    return CVUploadStatusResponse(
        upload_id=upload_id,
        progress=upload_batch.progress,
        status=upload_batch.status,
        files=files_status,
        total_files=upload_batch.total_files,
        processed_files=upload_batch.processed_files,
    )


@router.get("/{cv_id}", response_model=CVResponse)
async def get_cv(
    cv_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.uploaded_by == usuario.id,
    ).first()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el CV con id {cv_id}",
        )

    return CVResponse(
        id=cv.id,
        file_name=cv.file_name,
        file_type=cv.file_type,
        file_size=cv.file_size,
        uploaded_by=cv.uploader,
        uploaded_at=cv.uploaded_at,
        status=cv.status,
        extracted_text=cv.extracted_text,
        error_message=cv.error_message,
    )


@router.get("/{cv_id}/analysis", response_model=CVAnalysisResponse)
async def get_cv_analysis(
    cv_id: int,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    from models.analisis import Analisis
    from models.perfil_cargo import PerfilCargo

    cv = db.query(CV).filter(
        CV.id == cv_id,
        CV.uploaded_by == usuario.id,
    ).first()

    if not cv:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el CV con id {cv_id}",
        )

    analisis = db.query(Analisis).filter(
        Analisis.cv_id == cv_id,
    ).first()

    if not analisis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"El CV con id {cv_id} no tiene analisis realizado",
        )

    perfil = db.query(PerfilCargo).filter(
        PerfilCargo.id == analisis.perfil_id,
    ).first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Perfil de cargo con id {analisis.perfil_id} no encontrado",
        )

    return CVAnalysisResponse(
        id=analisis.id,
        cv_id=analisis.cv_id,
        perfil_id=analisis.perfil_id,
        perfil_titulo=perfil.titulo,
        puntaje=analisis.puntaje,
        etiqueta=analisis.etiqueta,
        feedback=analisis.feedback,
        analyzed_at=analisis.analyzed_at,
        analyzed_by=analisis.analyst,
    )


@router.post("/analysis/batch", response_model=BatchAnalysisStatusResponse, status_code=status.HTTP_200_OK)
async def batch_analysis(
    request: Request,
    request_data: BatchAnalysisRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    import uuid
    from models.analysis_batch import AnalysisBatch
    from models.perfil_cargo import PerfilCargo
    from models.analisis import Analisis

    perfil = db.query(PerfilCargo).filter(
        PerfilCargo.id == request_data.perfil_id,
    ).first()

    if not perfil:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el perfil de cargo con id {request_data.perfil_id}",
        )

    if request_data.cv_ids:
        cvs = db.query(CV).filter(
            CV.id.in_(request_data.cv_ids),
            CV.uploaded_by == usuario.id,
        ).all()

        if len(cvs) != len(request_data.cv_ids):
            found_ids = {cv.id for cv in cvs}
            missing_ids = set(request_data.cv_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CVs no encontrados: {missing_ids}",
            )
    else:
        cvs = db.query(CV).filter(
            CV.uploaded_by == usuario.id,
        ).all()

    if not cvs:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No hay CVs para analizar. Proporcione cv_ids validos o suba CVs primero.",
        )

    batch_id = str(uuid.uuid4())
    estimated_time = len(cvs) * 10

    analysis_batch = AnalysisBatch(
        batch_id=batch_id,
        perfil_id=request_data.perfil_id,
        status="processing",
        total_cvs=len(cvs),
        processed_cvs=0,
        estimated_time_seconds=estimated_time,
        created_by=usuario.id,
    )
    db.add(analysis_batch)
    db.commit()
    db.refresh(analysis_batch)

    resultados = []

    # Determinar el analizador a usar (GROQ como principal, Local como fallback)
    groq_api_key = settings.groq_api_key or os.getenv('GROQ_API_KEY', '')
    if groq_api_key:
        logger.info(f"Usando GROQ con API key: {groq_api_key[:5]}...{groq_api_key[-4:]}")
        analizador = GroqAdapter(api_key=groq_api_key)
    else:
        logger.warning("GROQ_API_KEY no configurada, usando LocalAdapter")
        analizador = LocalAdapter()

    for cv in cvs:
        try:
            if not cv.extracted_text:
                logger.warning(f"CV {cv.id} no tiene texto extraido. Saltando analisis.")
                continue

            # Verificar si ya existe analisis para este CV con este perfil
            existe_analisis = db.query(Analisis).filter(
                Analisis.cv_id == cv.id,
                Analisis.perfil_id == request_data.perfil_id,
            ).first()

            if existe_analisis:
                # CV ya analizado con este perfil, retornar resultado existente
                logger.info(f"CV {cv.id} ya fue analizado con perfil {request_data.perfil_id}, usando resultado existente")
                resultados.append({
                    "cv_id": cv.id,
                    "file_name": cv.file_name,
                    "puntaje": existe_analisis.puntaje,
                    "etiqueta": existe_analisis.etiqueta,
                    "feedback": existe_analisis.feedback,
                    "existing": True,
                })
                analysis_batch.processed_cvs += 1
                continue

            # Procesar nuevo analisis
            try:
                resultado_ia = await analizador.analizar_cv(
                    cv_texto=cv.extracted_text,
                    perfil_titulo=perfil.titulo,
                    perfil_descripcion=perfil.descripcion,
                    perfil_puntos_fuertes=perfil.habilidades_requeridas,
                    perfil=perfil,
                )
                puntaje = resultado_ia.puntaje
                etiqueta = resultado_ia.etiqueta
                feedback = resultado_ia.feedback
                fortalezas = resultado_ia.fortalezas
                debilidades = resultado_ia.debilidades
            except Exception as e:
                logger.error(f"Error con analizador {type(analizador).__name__}: {e}, usando fallback LocalAdapter")
                fallback = LocalAdapter()
                resultado_ia = await fallback.analizar_cv(
                    cv_texto=cv.extracted_text,
                    perfil_titulo=perfil.titulo,
                    perfil_descripcion=perfil.descripcion,
                    perfil_puntos_fuertes=perfil.habilidades_requeridas,
                    perfil=perfil,
                )
                puntaje = resultado_ia.puntaje
                etiqueta = resultado_ia.etiqueta
                feedback = resultado_ia.feedback
                fortalezas = resultado_ia.fortalezas
                debilidades = resultado_ia.debilidades

            # Segundo check: verificar nuevamente antes de insertar (evita race condition)
            existe_analisis_ahora = db.query(Analisis).filter(
                Analisis.cv_id == cv.id,
                Analisis.perfil_id == request_data.perfil_id,
            ).first()

            if existe_analisis_ahora:
                # Otro request ya insertó el análisis, usar ese resultado
                logger.info(f"CV {cv.id} ya fue analizado con perfil {request_data.perfil_id} (race condition), usando resultado existente")
                resultados.append({
                    "cv_id": cv.id,
                    "file_name": cv.file_name,
                    "puntaje": existe_analisis_ahora.puntaje,
                    "etiqueta": existe_analisis_ahora.etiqueta,
                    "feedback": existe_analisis_ahora.feedback,
                    "existing": True,
                })
                analysis_batch.processed_cvs += 1
                continue

            # Guardar nuevo analisis
            analisis = Analisis(
                cv_id=cv.id,
                perfil_id=request_data.perfil_id,
                analysis_batch_id=analysis_batch.id,
                puntaje=puntaje,
                etiqueta=etiqueta,
                feedback=feedback,
                fortalezas=json.dumps(fortalezas),
                debilidades=json.dumps(debilidades),
                analyzed_by=usuario.id,
            )
            db.add(analisis)
            resultados.append({
                "cv_id": cv.id,
                "file_name": cv.file_name,
                "puntaje": puntaje,
                "etiqueta": etiqueta,
                "feedback": feedback,
            })
            analysis_batch.processed_cvs += 1

        except Exception as e:
            logger.error(f"Error al analizar CV {cv.id}: {e}")
            resultados.append({
                "cv_id": cv.id,
                "file_name": cv.file_name,
                "error": str(e),
            })

    analysis_batch.status = "completed"
    db.commit()

    logger.info(f"Batch analysis {batch_id}: {len(resultados)} CVs analizados")

    return BatchAnalysisStatusResponse(
        batch_id=batch_id,
        status="completed",
        total_cvs=len(cvs),
        processed_cvs=len(resultados),
        progress=100 if cvs else 0,
        results=resultados,
    )


@router.get("/analysis/batch-status/{batch_id}", response_model=BatchAnalysisStatusResponse)
async def get_batch_status(
    batch_id: str,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    from models.analysis_batch import AnalysisBatch
    from models.analisis import Analisis

    analysis_batch = db.query(AnalysisBatch).filter(
        AnalysisBatch.batch_id == batch_id,
        AnalysisBatch.created_by == usuario.id,
    ).first()

    if not analysis_batch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No se encontro el batch de analisis con id {batch_id}",
        )

    analisis_list = db.query(Analisis).join(Analisis.cv).filter(
        Analisis.analysis_batch_id == analysis_batch.id,
    ).all()

    results = [
        {
            "cv_id": a.cv.id,
            "file_name": a.cv.file_name,
            "puntaje": a.puntaje,
            "etiqueta": a.etiqueta,
            "feedback": a.feedback,
        }
        for a in analisis_list
    ]

    return BatchAnalysisStatusResponse(
        batch_id=batch_id,
        status=analysis_batch.status,
        total_cvs=analysis_batch.total_cvs,
        processed_cvs=analysis_batch.processed_cvs,
        progress=analysis_batch.progress,
        results=results if analysis_batch.status == "completed" else None,
    )


@router.get("/list")
async def list_cvs(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    cvs = db.query(CV).filter(
        CV.uploaded_by == usuario.id,
    ).order_by(CV.uploaded_at.desc()).all()

    cvs_data = [
        {
            "id": cv.id,
            "file_name": cv.file_name,
            "file_type": cv.file_type,
            "file_size": cv.file_size,
            "uploaded_at": cv.uploaded_at.isoformat() if cv.uploaded_at else None,
            "status": cv.status,
            "candidate_name": cv.candidate_name,
            "candidate_email": cv.candidate_email,
            "candidate_phone": cv.candidate_phone,
            "candidate_summary": cv.candidate_summary,
        }
        for cv in cvs
    ]

    return cvs_data


@router.get("/list-html")
async def list_cvs_html(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    cvs = db.query(CV).filter(
        CV.uploaded_by == usuario.id,
    ).order_by(CV.uploaded_at.desc()).all()

    html_table = '''<table class="min-w-full divide-y divide-gray-200">
      <thead class="bg-gray-50">
        <tr>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Archivo</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Candidato</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
          <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Fecha</th>
        </tr>
      </thead>
      <tbody class="bg-white divide-y divide-gray-200">'''

    if not cvs:
        html_table += '''<tr><td colspan="4" class="px-6 py-4 text-center text-gray-500">No hay CVs subidos aun</td></tr>'''
    else:
        for cv in cvs:
            fecha_formateada = cv.uploaded_at.strftime('%d/%m/%Y') if cv.uploaded_at else 'N/A'

            html_table += f'''
            <tr class="hover:bg-gray-50">
              <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{cv.file_name}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{cv.candidate_name or 'N/A'}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{cv.candidate_email or 'N/A'}</td>
              <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-700">{fecha_formateada}</td>
            </tr>'''

    html_table += '''</tbody>
    </table>'''

    return HTMLResponse(content=html_table)


from pydantic import BaseModel

class BatchDeleteRequest(BaseModel):
    cv_ids: list[int]


@router.delete("/batch")
async def batch_delete_cvs(
    request: BatchDeleteRequest,
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    try:
        if not request.cv_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se proporcionaron CVs para eliminar",
            )

        cvs = db.query(CV).filter(
            CV.id.in_(request.cv_ids),
            CV.uploaded_by == usuario.id,
        ).all()

        if len(cvs) != len(request.cv_ids):
            found_ids = {cv.id for cv in cvs}
            missing_ids = set(request.cv_ids) - found_ids
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"CVs no encontrados o no pertenecen al usuario: {missing_ids}",
            )

        db.query(Analisis).filter(
            Analisis.cv_id.in_(request.cv_ids)
        ).delete(synchronize_session=False)

        db.query(CV).filter(
            CV.id.in_(request.cv_ids)
        ).delete(synchronize_session=False)

        db.commit()

        return {
            "success": True,
            "deleted": len(request.cv_ids),
            "message": f"{len(request.cv_ids)} CV(s) eliminados correctamente",
        }

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error al eliminar CVs en lote: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno al eliminar los CVs",
        )
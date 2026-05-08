"""
Rutas de API para gestión de candidatos (CVs individuales).
"""
import logging
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from api.deps import get_db, require_auth
from core.config import settings
from models.cv import CV
from models.usuario import Usuario

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/candidates", tags=["Candidatos"])

# Directorio de uploads
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "cvs"


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_candidate_cv(
    file: UploadFile = File(..., description="Archivo CV en formato PDF"),
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(require_auth),
):
    """
    Sube un único archivo CV (PDF) para procesamiento.

    - Acepta **multipart/form-data** con un archivo PDF
    - Valida tipo y tamaño del archivo
    - Guarda metadatos en base de datos
    - Guarda el archivo en disco

    **Extensión soportada**: .pdf
    **Tamaño máximo**: 10MB
    """
    # Validar extensión
    file_ext = Path(file.filename or "").suffix.lower()
    if file_ext != ".pdf":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tipo de archivo no soportado: {file_ext}. Solo se aceptan archivos PDF",
        )

    # Verificar tamaño leyendo el contenido
    content = await file.read()
    size = len(content)
    
    # Resetear el archivo para lectura posterior
    file.file.seek(0)

    if size > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Archivo demasiado grande ({size / 1024 / 1024:.2f}MB). Máximo {settings.max_file_size_mb}MB",
        )

    if size == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo está vacío",
        )

    # Crear directorio de uploads si no existe
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    # Generar nombre único para el archivo
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename

    try:
        # Guardar archivo en disco (content ya fue leído arriba)
        with open(file_path, "wb") as f:
            f.write(content)

        # Crear registro en base de datos
        cv = CV(
            file_name=file.filename or "unknown",
            file_type="pdf",
            file_size=size,
            uploaded_by=usuario.id,
            status="uploaded",
            uploaded_at=datetime.utcnow(),
        )
        db.add(cv)
        db.commit()
        db.refresh(cv)

        logger.info(f"CV subido: {file.filename} (id={cv.id}, usuario={usuario.id})")

        return {
            "success": True,
            "message": "CV subido exitosamente",
            "cv_id": cv.id,
            "file_name": file.filename,
            "file_size": size,
        }

    except Exception as e:
        logger.error(f"Error al subir CV: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al subir el archivo: {str(e)}",
        )

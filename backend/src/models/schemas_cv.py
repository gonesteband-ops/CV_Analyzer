"""
Schemas Pydantic para CVs y uploads.
"""
from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class CVFileUploadResponse(BaseModel):
    """Schema para respuesta de archivo CV subido."""

    file_name: str
    file_id: int
    status: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None


class CVUploadResponse(BaseModel):
    """Schema para respuesta de upload múltiple de CVs."""

    upload_id: str
    status: str
    files: list[CVFileUploadResponse]
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "uuid-1234-5678",
                "status": "processing",
                "files": [
                    {"file_name": "cv1.pdf", "file_id": 101, "status": "uploaded"},
                    {"file_name": "cv2.docx", "file_id": 102, "status": "uploaded"}
                ]
            }
        }


class CVUploadStatusResponse(BaseModel):
    """Schema para respuesta de estado de upload."""

    upload_id: str
    progress: int = Field(..., ge=0, le=100, description="Progreso en porcentaje")
    status: str
    files: list[CVFileUploadResponse]
    total_files: int
    processed_files: int

    class Config:
        json_schema_extra = {
            "example": {
                "upload_id": "uuid-1234-5678",
                "progress": 75,
                "status": "parsing",
                "files": [
                    {"file_id": 101, "file_name": "cv1.pdf", "status": "parsed"},
                    {"file_id": 102, "file_name": "cv2.docx", "status": "parsing"}
                ],
                "total_files": 2,
                "processed_files": 1
            }
        }


class UsuarioMinimalResponse(BaseModel):
    """Schema minimal de usuario para respuestas anidadas."""

    id: int
    nombre: str
    email: str

    class Config:
        from_attributes = True


class CVResponse(BaseModel):
    """Schema para respuesta de CV individual."""

    id: int
    file_name: str
    file_type: str
    file_size: int
    uploaded_by: UsuarioMinimalResponse
    uploaded_at: datetime
    status: str
    extracted_text: Optional[str] = None
    error_message: Optional[str] = None

    class Config:
        from_attributes = True


class CVAnalysisResponse(BaseModel):
    """Schema para respuesta de análisis de CV."""

    id: int
    cv_id: int
    perfil_id: int
    perfil_titulo: str
    puntaje: int
    etiqueta: str
    feedback: str
    analyzed_at: datetime
    analyzed_by: UsuarioMinimalResponse

    class Config:
        from_attributes = True


class BatchAnalysisRequest(BaseModel):
    """Schema para petición de análisis masivo."""

    perfil_id: int
    cv_ids: Optional[list[int]] = None  # Si es None, analiza todos los CVs pendientes

    class Config:
        json_schema_extra = {
            "example": {
                "perfil_id": 1,
                "cv_ids": [101, 102, 103]
            }
        }


class BatchAnalysisStatusResponse(BaseModel):
    """Schema para respuesta de estado de análisis masivo."""

    batch_id: str
    progress: int = Field(..., ge=0, le=100)
    status: str  # pending, processing, completed, error
    total_cvs: int
    processed_cvs: int
    results: Optional[list[dict]] = None

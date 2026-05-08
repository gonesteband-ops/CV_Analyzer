# API Contracts: AI-Recruiter Pro

**Feature**: 001-ai-recruiter-pro | **Date**: 2026-04-23
**Purpose**: Define external API contracts for frontend-backend communication

---

## Authentication API

### POST /api/auth/login

**Purpose**: Authenticate user with email/password

**Request**:
```json
{
  "email": "reclutador@callcenter.cl",
  "password": "Password123"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "user": {
    "id": 1,
    "email": "reclutador@callcenter.cl",
    "nombre": "María González",
    "rol": "reclutador"
  },
  "redirect": "/inicio"
}
```

**Response (401 Unauthorized)**:
```json
{
  "success": false,
  "error": "Credenciales inválidas"
}
```

**Errors**:
- 400: Email format invalid
- 401: Invalid credentials
- 429: Too many failed attempts (rate limiting)

---

### POST /api/auth/logout

**Purpose**: End user session

**Request**: No body (session from cookie)

**Response (200 OK)**:
```json
{
  "success": true,
  "redirect": "/login"
}
```

---

### POST /api/auth/recover

**Purpose**: Request password recovery email

**Request**:
```json
{
  "email": "reclutador@callcenter.cl"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Si el email existe, se enviaron instrucciones de recuperación"
}
```

**Note**: Always return success to prevent email enumeration attacks

---

### POST /api/auth/reset

**Purpose**: Reset password with recovery token

**Request**:
```json
{
  "token": "uuid-token-from-email",
  "new_password": "NewPassword123"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "Contraseña actualizada exitosamente"
}
```

**Errors**:
- 400: Invalid token format
- 401: Token expired or invalid
- 400: Password doesn't meet requirements

---

## CV Management API

### POST /api/cvs/upload

**Purpose**: Upload multiple CV files

**Request**: `multipart/form-data`
```
files: <file1.pdf>, <file2.docx>, <file3.txt>
```

**Response (202 Accepted)**:
```json
{
  "upload_id": "uuid-123",
  "status": "processing",
  "files": [
    {"file_name": "cv1.pdf", "file_id": 101, "status": "uploaded"},
    {"file_name": "cv2.docx", "file_id": 102, "status": "uploaded"}
  ]
}
```

**Progress Polling**: GET /api/cvs/upload-status/{upload_id}

**Response (200 OK)**:
```json
{
  "upload_id": "uuid-123",
  "progress": 75,
  "status": "parsing",
  "files": [
    {"file_id": 101, "status": "parsed"},
    {"file_id": 102, "status": "parsing"}
  ]
}
```

**Errors**:
- 400: No files provided
- 413: File too large (>10MB)
- 415: Unsupported file type

---

### GET /api/cvs/{id}

**Purpose**: Get CV details

**Response (200 OK)**:
```json
{
  "id": 101,
  "file_name": "juan_perez_cv.pdf",
  "file_type": ".pdf",
  "file_size": 245678,
  "uploaded_at": "2026-04-23T14:30:00-03:00",
  "uploaded_by": {
    "id": 1,
    "nombre": "María González"
  },
  "status": "analyzed",
  "extracted_text": "Juan Pérez\nExperiencia: 5 años en ventas..."
}
```

---

### GET /api/cvs/{id}/analysis

**Purpose**: Get analysis result for a CV

**Response (200 OK)**:
```json
{
  "id": 501,
  "cv_id": 101,
  "perfil_id": 3,
  "perfil_titulo": "Ejecutivo de Ventas",
  "puntaje": 85,
  "etiqueta": "Recomendado",
  "feedback": "El candidato demuestra sólida experiencia en ventas telefónicas...",
  "analyzed_at": "2026-04-23T14:35:00-03:00"
}
```

**Response (404 Not Found)**:
```json
{
  "error": "Análisis no encontrado para este CV"
}
```

---

### DELETE /api/cvs/{id}

**Purpose**: Delete a CV (soft delete)

**Response (200 OK)**:
```json
{
  "success": true,
  "message": "CV eliminado exitosamente"
}
```

---

## Profile Management API

### GET /api/profiles

**Purpose**: List all job profiles

**Response (200 OK)**:
```json
{
  "profiles": [
    {
      "id": 1,
      "titulo": "Ejecutivo SAC",
      "descripcion": "Atención al cliente vía telefónica...",
      "puntos_fuertes": ["Experiencia en call center", "Manejo de CRM"],
      "created_at": "2026-04-20T10:00:00-03:00"
    },
    {
      "id": 2,
      "titulo": "Ejecutivo de Ventas",
      "descripcion": "Venta telefónica de productos...",
      "puntos_fuertes": ["Experiencia en ventas", "Manejo de objeciones"],
      "created_at": "2026-04-21T11:30:00-03:00"
    }
  ]
}
```

---

### POST /api/profiles

**Purpose**: Create new job profile

**Request**:
```json
{
  "titulo": "Cobranzas",
  "descripcion": "Gestión de cartera vencida mediante llamadas y gestiones extrajudiciales...",
  "puntos_fuertes": [
    "Experiencia en cobranza telefónica",
    "Conocimiento legislación laboral",
    "Manejo de estrés"
  ]
}
```

**Response (201 Created)**:
```json
{
  "success": true,
  "profile": {
    "id": 3,
    "titulo": "Cobranzas",
    "descripcion": "Gestión de cartera vencida...",
    "puntos_fuertes": ["Experiencia en cobranza telefónica", ...],
    "created_at": "2026-04-23T15:00:00-03:00"
  }
}
```

**Errors**:
- 400: Missing required fields
- 400: puntos_fuertes empty or >20 items

---

### GET /api/profiles/{id}

**Purpose**: Get profile details

**Response (200 OK)**:
```json
{
  "id": 1,
  "titulo": "Ejecutivo SAC",
  "descripcion": "Atención al cliente...",
  "puntos_fuertes": ["Experiencia en call center", "Manejo de CRM", "Inglés intermedio"],
  "created_by": {
    "id": 1,
    "nombre": "María González"
  },
  "created_at": "2026-04-20T10:00:00-03:00"
}
```

---

### PUT /api/profiles/{id}

**Purpose**: Update existing profile

**Request**:
```json
{
  "titulo": "Ejecutivo SAC Senior",
  "descripcion": "Atención al cliente vía telefónica y digital, manejo de casos complejos...",
  "puntos_fuertes": ["Experiencia en call center", "Manejo de CRM", "Inglés avanzado"]
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "profile": {
    "id": 1,
    "titulo": "Ejecutivo SAC Senior",
    "descripcion": "Atención al cliente...",
    "puntos_fuertes": [...],
    "updated_at": "2026-04-23T15:30:00-03:00"
  }
}
```

---

### DELETE /api/profiles/{id}

**Purpose**: Delete job profile

**Response (400 Bad Request)**:
```json
{
  "error": "No se puede eliminar el perfil: tiene 15 análisis asociados"
}
```

**Note**: Profiles with analyses cannot be deleted (RESTRICT)

---

## Analysis API

### POST /api/analysis/batch

**Purpose**: Trigger batch analysis for uploaded CVs

**Request**:
```json
{
  "cv_ids": [101, 102, 103],
  "perfil_id": 2
}
```

**Response (202 Accepted)**:
```json
{
  "batch_id": "batch-456",
  "status": "processing",
  "total": 3,
  "processed": 0,
  "estimated_time_seconds": 30
}
```

**Progress Polling**: GET /api/analysis/batch-status/{batch_id}

**Response (200 OK)**:
```json
{
  "batch_id": "batch-456",
  "status": "completed",
  "total": 3,
  "processed": 3,
  "results": [
    {"cv_id": 101, "puntaje": 85, "etiqueta": "Recomendado"},
    {"cv_id": 102, "puntaje": 62, "etiqueta": "Recomendado con reservas"},
    {"cv_id": 103, "puntaje": 35, "etiqueta": "No Recomendado"}
  ]
}
```

---

### GET /api/analysis/results

**Purpose**: Get paginated analysis results with filters

**Query Parameters**:
- `perfil_id` (optional): Filter by profile
- `etiqueta` (optional): Filter by tag
- `min_puntaje` (optional): Minimum score
- `max_puntaje` (optional): Maximum score
- `date_from` (optional): Start date (ISO 8601)
- `date_to` (optional): End date (ISO 8601)
- `search` (optional): Search candidate name
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20, max: 100)

**Response (200 OK)**:
```json
{
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "results": [
    {
      "id": 501,
      "cv": {
        "id": 101,
        "file_name": "juan_perez.pdf",
        "extracted_text_preview": "Juan Pérez, 5 años experiencia..."
      },
      "perfil": {
        "id": 2,
        "titulo": "Ejecutivo de Ventas"
      },
      "puntaje": 85,
      "etiqueta": "Recomendado",
      "feedback": "El candidato demuestra...",
      "analyzed_at": "2026-04-23T14:35:00-03:00",
      "analyzed_by": {
        "id": 1,
        "nombre": "María González"
      }
    }
  ]
}
```

---

### GET /api/history/export

**Purpose**: Export filtered results to XLSX

**Query Parameters**: Same as GET /api/analysis/results

**Response (200 OK)**: File download
- Content-Type: `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`
- Content-Disposition: `attachment; filename="analisis_cvs_2026-04-23.xlsx"`

**File Contents**:
- Sheet name: "Análisis CVs"
- Headers: Candidato, Perfil, Puntaje, Etiqueta, Fecha, Analizado por
- Color-coded score cells (green/yellow/red)
- Corporate blue header row

---

## Portal Configuration API

### GET /api/portals

**Purpose**: List configured job portals

**Response (200 OK)**:
```json
{
  "portals": [
    {
      "portal_name": "Laborum",
      "cliente_id": "client-123",
      "usuario": "api_user",
      "configured": true,
      "status": "ready",
      "updated_at": "2026-04-20T09:00:00-03:00"
    },
    {
      "portal_name": "Trabajando",
      "cliente_id": null,
      "usuario": null,
      "configured": false,
      "status": "pending",
      "updated_at": null
    }
  ]
}
```

**Note**: encrypted_secret is never returned

---

### PUT /api/portals/{portal_name}/credentials

**Purpose**: Update portal credentials

**Request**:
```json
{
  "cliente_id": "client-456",
  "usuario": "new_api_user",
  "secret": "plain_text_password"
}
```

**Response (200 OK)**:
```json
{
  "success": true,
  "portal": {
    "portal_name": "Laborum",
    "cliente_id": "client-456",
    "usuario": "new_api_user",
    "configured": true,
    "status": "ready",
    "updated_at": "2026-04-23T16:00:00-03:00"
  }
}
```

**Errors**:
- 400: Missing required fields
- 404: Portal name not found

---

## Error Response Format

All error responses follow this format:

```json
{
  "success": false,
  "error": "Mensaje de error descriptivo",
  "error_code": "INVALID_CREDENTIALS"
}
```

**Common Error Codes**:
- `INVALID_CREDENTIALS`: Login failed
- `TOKEN_EXPIRED`: Password reset token expired
- `FILE_TOO_LARGE`: Upload exceeds 10MB limit
- `UNSUPPORTED_FORMAT`: File type not PDF/DOCX/TXT
- `PROFILE_HAS_ANALYSIS`: Cannot delete profile with analyses
- `NOT_FOUND`: Resource doesn't exist
- `UNAUTHORIZED`: Authentication required
- `FORBIDDEN`: Insufficient permissions
- `RATE_LIMITED`: Too many requests

---

## HTMX-Specific Endpoints

These endpoints return HTML fragments for HTMX swaps:

### GET /components/upload-progress/{upload_id}

**Purpose**: Return progress bar HTML fragment

**Response (200 OK)**:
```html
<div id="progress-123" class="progress-container">
  <div class="progress-bar" style="width: 75%"></div>
  <span>75% - Procesando...</span>
</div>
```

---

### GET /components/results-table

**Purpose**: Return analysis results table fragment

**Response (200 OK)**:
```html
<table class="results-table">
  <thead>
    <tr>
      <th>Candidato</th>
      <th>Perfil</th>
      <th>Puntaje</th>
      <th>Etiqueta</th>
      <th>Fecha</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>Juan Pérez</td>
      <td>Ejecutivo de Ventas</td>
      <td>
        <div class="score-bar" style="background: linear-gradient(to right, #28a745 85%, #e0e0e0 85%)">
          85
        </div>
      </td>
      <td><span class="badge badge-success">Recomendado</span></td>
      <td>23-04-2026 14:35</td>
    </tr>
  </tbody>
</table>
```

---

## Versioning

API version: v1 (implicit, no URL prefix for v1)

Breaking changes will require:
- New version prefix: `/api/v2/...`
- Deprecation notice for v1 (90 days minimum)
- Migration guide documentation

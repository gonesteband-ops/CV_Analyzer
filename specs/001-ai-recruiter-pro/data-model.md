# Data Model: AI-Recruiter Pro

**Feature**: 001-ai-recruiter-pro | **Date**: 2026-04-23
**Source**: Derived from spec.md entities and requirements

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│   Usuario   │──────<│  Perfil de Cargo │       │   Usuario   │
├─────────────┤  1:N  ├──────────────────┤       ├─────────────┤
│ id          │       │ id               │       │ id          │
│ email       │       │ titulo           │       │ email       │
│ password    │       │ descripcion      │       │ password    │
│ nombre      │       │ puntos_fuertes   │       │ nombre      │
│ rol         │       │ created_by (FK)  │       │ rol         │
│ created_at  │       │ created_at       │       │ created_at  │
│ last_login  │       └──────────────────┘       │ last_login  │
└─────────────┘              │                    └─────────────┘
       │                     │ 1:N                        │
       │                     │                            │
       │                     ▼                            │
       │              ┌─────────────┐                     │
       │              │   Análisis  │                     │
       │              ├─────────────┤                     │
       │              │ id          │                     │
       │              │ cv_id (FK)  │>────────────────────┤
       │              │ perfil_id   │                     │
       │              │ puntaje     │                     │
       │              │ etiqueta    │                     │
       │              │ feedback    │                     │
       │              │ analyzed_at │                     │
       │              │ analyzed_by │                     │
       │              └─────────────┘                     │
       │                                                  │
       │ 1:N                                              │ 1:N
       │                                                  │
       ▼                                                  ▼
┌─────────────┐                                 ┌───────────────────┐
│     CV      │                                 │ PortalCredential  │
├─────────────┤                                 ├───────────────────┤
│ id          │                                 │ id                │
│ file_name   │                                 │ portal_name       │
│ file_type   │                                 │ cliente_id        │
│ file_size   │                                 │ usuario           │
│ uploaded_by │                                 │ encrypted_secret  │
│ uploaded_at │                                 │ updated_at        │
│ status      │                                 └───────────────────┘
│ extracted_text │
└─────────────┘
```

## Entity Specifications

### Usuario

**Purpose**: Representa reclutadores y gerentes con acceso al sistema

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | Integer | PK, auto-increment | Identificador único |
| email | String(255) | UNIQUE, NOT NULL, valid email format | Credencial de login |
| password_hash | String(255) | NOT NULL, min 8 chars (validated before hashing) | Contraseña encriptada (bcrypt) |
| nombre | String(255) | NOT NULL | Nombre para mensaje de bienvenida |
| rol | String(50) | NOT NULL, default "reclutador" | Rol: reclutador, administrador |
| created_at | DateTime | NOT NULL, default UTC now | Fecha de creación |
| last_login | DateTime | NULLABLE | Último acceso del usuario |

**Validation Rules**:
- Email debe tener formato válido (regex: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`)
- Email único en todo el sistema
- Password mínimo 8 caracteres, debe contener mayúsculas, minúsculas y números
- Rol debe ser uno de: ["reclutador", "administrador"]

**Indexes**:
- `idx_usuario_email` (UNIQUE)
- `idx_usuario_rol`

---

### Perfil de Cargo

**Purpose**: Define requisitos de cargo para comparar CVs

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | Integer | PK, auto-increment | Identificador único |
| titulo | String(255) | NOT NULL | Nombre del cargo (ej: "Ejecutivo de Ventas") |
| descripcion | Text | NOT NULL | Descripción detallada del rol |
| puntos_fuertes | JSON | NOT NULL, array de strings | Skills/requisitos clave (ej: ["Manejo SAP Hana 4", "Inglés B2"]) |
| created_by | Integer | FK → Usuario.id, NOT NULL | Usuario que creó el perfil |
| created_at | DateTime | NOT NULL, default UTC now | Fecha de creación |

**Validation Rules**:
- Título no puede estar vacío (min 3 caracteres)
- Descripción mínimo 20 caracteres
- puntos_fuertes debe tener al menos 1 elemento, máximo 20
- Cada punto fuerte máximo 100 caracteres

**Indexes**:
- `idx_perfil_created_by`
- `idx_perfil_titulo` (para búsqueda)

---

### CV

**Purpose**: Almacena metadata y contenido extraído de CVs subidos

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | Integer | PK, auto-increment | Identificador único |
| file_name | String(255) | NOT NULL | Nombre original del archivo |
| file_type | String(10) | NOT NULL, CHECK IN (".pdf", ".docx", ".txt") | Extensión del archivo |
| file_size | Integer | NOT NULL, > 0 | Tamaño en bytes |
| uploaded_by | Integer | FK → Usuario.id, NOT NULL | Usuario que subió el CV |
| uploaded_at | DateTime | NOT NULL, default UTC now | Fecha de subida |
| status | String(50) | NOT NULL, default "uploaded" | Estado: uploaded, parsing, parsed, analyzing, analyzed, failed |
| extracted_text | Text | NULLABLE | Contenido de texto extraído (TSV para búsqueda) |
| error_message | Text | NULLABLE | Mensaje de error si status = failed |

**Validation Rules**:
- file_type debe ser uno de: [".pdf", ".docx", ".txt"]
- file_size máximo 10MB (10,485,760 bytes)
- status transition válido: uploaded → parsing → parsed → analyzing → analyzed (o failed en cualquier punto)

**State Machine**:
```
uploaded → parsing → parsed → analyzing → analyzed
    │          │          │          │
    │          │          │          └─→ (terminal)
    │          │          │
    │          │          └─→ failed (terminal)
    │          │
    │          └─→ failed (terminal)
    │
    └─→ failed (terminal)
```

**Indexes**:
- `idx_cv_uploaded_by`
- `idx_cv_status`
- `idx_cv_uploaded_at`
- `idx_cv_extracted_text` (GIN para full-text search en PostgreSQL)

---

### Análisis

**Purpose**: Resultado de comparar un CV contra un perfil de cargo

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | Integer | PK, auto-increment | Identificador único |
| cv_id | Integer | FK → CV.id, NOT NULL, UNIQUE | CV analizado |
| perfil_id | Integer | FK → Perfil de Cargo.id, NOT NULL | Perfil usado para análisis |
| puntaje | Integer | NOT NULL, CHECK 0-100 | Score de emparejamiento |
| etiqueta | String(50) | NOT NULL | "Recomendado", "Recomendado con reservas", "No Recomendado", "Información Insuficiente" |
| feedback | Text | NOT NULL | Retroalimentación narrativa |
| analyzed_at | DateTime | NOT NULL, default UTC now | Fecha de análisis |
| analyzed_by | Integer | FK → Usuario.id, NOT NULL | Usuario que ejecutó análisis |

**Validation Rules**:
- puntaje debe estar entre 0 y 100
- etiqueta derivada de puntaje:
  - puntaje ≥ 70 → "Recomendado"
  - puntaje 40-69 → "Recomendado con reservas"
  - puntaje < 40 → "No Recomendado"
  - CV con texto insuficiente → "Información Insuficiente" (sin puntaje numérico)
- feedback mínimo 50 caracteres
- Un CV solo puede tener un análisis por perfil (unique constraint: cv_id + perfil_id)

**Indexes**:
- `idx_analisis_cv_id` (UNIQUE)
- `idx_analisis_perfil_id`
- `idx_analisis_analyzed_at`
- `idx_analisis_etiqueta`
- `idx_analisis_puntaje`

---

### PortalCredential

**Purpose**: Almacena credenciales encriptadas para portales de empleo

| Campo | Tipo | Restricciones | Descripción |
|-------|------|---------------|-------------|
| id | Integer | PK, auto-increment | Identificador único |
| portal_name | String(50) | UNIQUE, NOT NULL | Nombre: "Laborum", "Trabajando" |
| cliente_id | String(255) | NOT NULL | ID de cliente provisto por portal |
| usuario | String(255) | NOT NULL | Usuario de API |
| encrypted_secret | String(512) | NOT NULL | Contraseña/token encriptado (Fernet) |
| updated_at | DateTime | NOT NULL, default UTC now on update | Última actualización |

**Validation Rules**:
- portal_name debe ser uno de: ["Laborum", "Trabajando"]
- encrypted_secret debe ser desencriptable (validar al guardar)
- Solo un registro por portal_name

**Security**:
- encrypted_secret usa Fernet encryption (symmetric)
- Encryption key stored in environment variable `CREDENTIAL_ENCRYPTION_KEY`
- Never log or expose encrypted_secret in API responses

**Indexes**:
- `idx_portal_name` (UNIQUE)

---

## Relationships Summary

| Parent | Child | Type | Cascade |
|--------|-------|------|---------|
| Usuario | Perfil de Cargo | 1:N | ON DELETE CASCADE (perfiles creados por usuario eliminado) |
| Usuario | CV | 1:N | ON DELETE SET NULL (preservar CVs, mostrar "Usuario eliminado") |
| Usuario | Análisis | 1:N | ON DELETE SET NULL |
| Perfil de Cargo | Análisis | 1:N | ON DELETE RESTRICT (no eliminar perfiles con análisis) |
| CV | Análisis | 1:1 | ON DELETE CASCADE (eliminar análisis si se elimina CV) |

---

## Database Schema (SQLAlchemy Models)

```python
# backend/src/models/usuario.py
class Usuario(Base):
    __tablename__ = "usuario"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    nombre = Column(String(255), nullable=False)
    rol = Column(String(50), nullable=False, default="reclutador")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    perfiles = relationship("PerfilCargo", back_populates="creator", cascade="all, delete-orphan")
    cvs = relationship("CV", back_populates="uploader", cascade="all, delete-orphan")
    analisis = relationship("Analisis", back_populates="analyst")


# backend/src/models/perfil_cargo.py
class PerfilCargo(Base):
    __tablename__ = "perfil_cargo"
    
    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(255), nullable=False)
    descripcion = Column(Text, nullable=False)
    puntos_fuertes = Column(JSON, nullable=False, default=list)
    created_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Relationships
    creator = relationship("Usuario", back_populates="perfiles")
    analisis = relationship("Analisis", back_populates="perfil")


# backend/src/models/cv.py
class CV(Base):
    __tablename__ = "cv"
    
    id = Column(Integer, primary_key=True, index=True)
    file_name = Column(String(255), nullable=False)
    file_type = Column(String(10), nullable=False)
    file_size = Column(Integer, nullable=False)
    uploaded_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    uploaded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    status = Column(String(50), nullable=False, default="uploaded")
    extracted_text = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    uploader = relationship("Usuario", back_populates="cvs")
    analisis = relationship("Analisis", back_populates="cv", uselist=False, cascade="all, delete-orphan")


# backend/src/models/analisis.py
class Analisis(Base):
    __tablename__ = "analisis"
    
    id = Column(Integer, primary_key=True, index=True)
    cv_id = Column(Integer, ForeignKey("cv.id"), nullable=False, unique=True)
    perfil_id = Column(Integer, ForeignKey("perfil_cargo.id"), nullable=False)
    puntaje = Column(Integer, nullable=False, CheckConstraint("puntaje >= 0 AND puntaje <= 100"))
    etiqueta = Column(String(50), nullable=False)
    feedback = Column(Text, nullable=False)
    analyzed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    analyzed_by = Column(Integer, ForeignKey("usuario.id"), nullable=False)
    
    # Relationships
    cv = relationship("CV", back_populates="analisis")
    perfil = relationship("PerfilCargo", back_populates="analisis")
    analyst = relationship("Usuario", back_populates="analisis")


# backend/src/models/portal_credential.py
class PortalCredential(Base):
    __tablename__ = "portal_credential"
    
    id = Column(Integer, primary_key=True, index=True)
    portal_name = Column(String(50), unique=True, nullable=False)
    cliente_id = Column(String(255), nullable=False)
    usuario = Column(String(255), nullable=False)
    encrypted_secret = Column(String(512), nullable=False)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
```

---

## Migration Order

1. **001_create_usuario_table** - Base users table
2. **002_create_perfil_cargo_table** - Job profiles (depends on usuario)
3. **003_create_cv_table** - CV storage (depends on usuario)
4. **004_create_analisis_table** - Analysis results (depends on cv, perfil_cargo, usuario)
5. **005_create_portal_credential_table** - Portal credentials (independent)
6. **006_add_full_text_search_indexes** - Search optimization (PostgreSQL-specific)

---

## Test Data Fixtures

```python
# backend/tests/fixtures.py

USUARIO_FIXTURES = [
    {
        "email": "reclutador@callcenter.cl",
        "password_hash": "$2b$12$...",  # bcrypt hash of "Password123"
        "nombre": "María González",
        "rol": "reclutador"
    },
    {
        "email": "admin@callcenter.cl",
        "password_hash": "$2b$12$...",
        "nombre": "Carlos Muñoz",
        "rol": "administrador"
    }
]

PERFIL_FIXTURES = [
    {
        "titulo": "Ejecutivo SAC",
        "descripcion": "Atención al cliente vía telefónica y digital",
        "puntos_fuertes": ["Experiencia en call center", "Manejo de CRM", "Inglés intermedio"]
    },
    {
        "titulo": "Ejecutivo de Ventas",
        "descripcion": "Venta telefónica de productos financieros",
        "puntos_fuertes": ["Experiencia en ventas", "Manejo de objeciones", "Metas cumplidas"]
    },
    {
        "titulo": "Cobranzas",
        "descripcion": "Gestión de cartera vencida",
        "puntos_fuertes": ["Negociación", "Manejo de estrés", "Legislación laboral"]
    }
]
```

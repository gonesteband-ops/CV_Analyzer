# Plan de Implementación: AI-Recruiter Pro

**Rama**: `001-ai-recruiter-pro` | **Fecha**: 2026-04-23 | **Spec**: [spec.md](spec.md)
**Input**: Especificación funcional de `/specs/001-ai-recruiter-pro/spec.md`

## Resumen

Sistema de automatización de revisión masiva de CVs para call centers que clasifica candidatos usando IA híbrida (embeddings 70% + keywords 30%) con arquitectura de adapters para cambio dinámico de proveedor. Incluye carga drag-and-drop, análisis asíncrono con reintentos, ranking configurable por perfil, y exportación XLSX corporativa.

## Contexto Técnico

**Lenguaje/Versión**: Python 3.11+
**Dependencias Principales**: FastAPI, SQLAlchemy, Pydantic, HTMX, Tailwind CSS v4
**Almacenamiento**: SQLite (desarrollo), PostgreSQL (producción)
**Testing**: pytest, pytest-asyncio, httpx
**Plataforma Objetivo**: Web browser (Chrome, Firefox, Edge, Safari), servidor Windows/Linux
**Tipo de Proyecto**: Web application (backend API + server-rendered frontend con HTMX)
**Objetivos de Performance**: 50 CVs en <5 min, búsquedas <2s para 10k registros, 10+ usuarios concurrentes
**Restricciones**: Colores corporativos (#2F4DAA, #4CAA37, #F95E50), fondo #F0F1F3, tipografía Inter, scrollbars 6px
**Escala/Alcance**: 10k+ CVs en histórico, 10+ usuarios concurrentes, 5 tipos de perfil base

## Verificación de Constitución

*GATE: Debe pasar antes de investigación Phase 0. Re-verificar después de Phase 1.*

**Estado**: No hay archivo `.specify/memory/constitution.md`

**Gates Aplicados (Best Practices por Defecto)**:

1. **Test-First**: Tests antes de implementación (TDD opcional pero recomendado)
2. **Type Hints**: Obligatorio en todo código Python
3. **Español**: Todo código, comentarios y documentación en español
4. **UI Corporativa**: Respetar paleta de colores y diseño Buk Enterprise
5. **Seguridad**: Hash de contraseñas (bcrypt), encriptación de credenciales (Fernet)

**Evaluación de Gates**: ✅ PASSED - El plan cumple con todos los gates por defecto

## Estructura del Proyecto

### Documentación (este feature)

```text
specs/001-ai-recruiter-pro/
├── plan.md              # Este archivo
├── research.md          # Phase 0 (completado en clarificación)
├── data-model.md        # Phase 1 (ya existe)
├── quickstart.md        # Phase 1 (ya existe)
├── contracts/           # Phase 1 (ya existe api.md)
└── tasks.md             # Phase 2 (creado por /speckit.tasks)
```

### Código Fuente (raíz del repositorio)

```text
backend/
├── src/
│   ├── api/
│   │   ├── routes/
│   │   │   ├── auth.py          # Login, logout, recuperación password
│   │   │   ├── cvs.py           # Upload, análisis, resultados
│   │   │   ├── profiles.py      # CRUD perfiles de cargo
│   │   │   ├── portals.py       # Credenciales portales
│   │   │   └── history.py       # Tabla histórica, filtros, export
│   │   ├── middleware/
│   │   │   └── auth.py          # Middleware de autenticación
│   │   └── deps.py              # Dependencias FastAPI
│   ├── models/
│   │   ├── usuario.py           # Modelo Usuario
│   │   ├── perfil_cargo.py      # Modelo PerfilCargo (con umbrales)
│   │   ├── cv.py                # Modelo CV
│   │   ├── analisis.py          # Modelo Analisis
│   │   └── portal_credential.py # Modelo PortalCredential
│   ├── services/
│   │   ├── ia_analyzer/
│   │   │   ├── base.py          # IAnalizadorIA (interface)
│   │   │   ├── deepseek.py      # DeepseekAdapter
│   │   │   ├── openai.py        # OpenAIAdapter (futuro)
│   │   │   └── local.py         # LocalAdapter (fallback)
│   │   ├── cv_parser.py         # Extracción texto PDF/DOCX/TXT
│   │   ├── matching.py          # Algoritmo híbrido 70/30
│   │   ├── auth_service.py      # Lógica de autenticación
│   │   └── export_service.py    # Generación XLSX corporativo
│   ├── core/
│   │   ├── config.py            # Configuración y settings
│   │   ├── security.py          # Hash, encriptación
│   │   ├── database.py          # Conexión DB, sesiones
│   │   └── retry.py             # Cola de reintentos con backoff
│   └── templates/
│       ├── layouts/
│       │   └── base.html        # Layout base con sidebar
│       ├── pages/
│       │   ├── login.html       # Login con background Buk
│       │   ├── home.html        # Dashboard + upload zone
│       │   ├── perfiles.html    # Formulario creación perfiles
│       │   ├── portales.html    # Configuración portales
│       │   └── historico.html   # Tabla con filtros + export
│       └── components/
│           ├── sidebar.html     # Navegación izquierda
│           ├── upload_zone.html # Drag-and-drop
│           ├── progress_bar.html # Progreso por archivo
│           ├── results_table.html # Tabla de resultados
│           └── score_badge.html  # Badge con color por puntaje
├── static/
│   ├── css/
│   │   └── styles.css           # Tailwind compilado
│   └── js/
│       └── htmx-config.js       # Configuración HTMX
├── tests/
│   ├── unit/
│   │   ├── test_cv_parser.py
│   │   ├── test_ia_analyzer.py
│   │   ├── test_matching.py
│   │   ├── test_auth_service.py
│   │   └── test_export_service.py
│   ├── integration/
│   │   ├── test_auth_routes.py
│   │   ├── test_cv_routes.py
│   │   ├── test_profile_routes.py
│   │   └── test_history_routes.py
│   └── contract/
│       └── test_api_contracts.py
├── pyproject.toml               # Dependencias, Ruff, Black
└── .env.example                 # Variables de entorno
```

**Decisión de Estructura**: Single project con backend/ conteniendo API y frontend server-rendered. HTMX maneja interacciones asíncronas sin build step.

## Tracking de Complejidad

> **Completar SOLO si hay violaciones de Constitución que justificar**

| Violación | Por Qué es Necesaria | Alternativa Simple Rechazada Porque |
|-----------|---------------------|-------------------------------------|
| N/A - Sin violaciones | - | - |

## Phase 0: Investigación (COMPLETADA)

**Estado**: ✅ COMPLETADA durante `/speckit.clarify`

Las siguientes decisiones ya fueron resueltas:

| Área | Decisión |
|------|----------|
| **Arquitectura IA** | Adapter pattern con `IAnalizadorIA` |
| **Algoritmo** | 70% embeddings + 30% keywords |
| **Umbrales** | Configurables por perfil |
| **Fallos IA** | 3 reintentos con backoff exponencial |
| **Exportación** | XLSX corporativo completo |

**No se requiere research.md adicional** - las clarificaciones ya documentaron las decisiones.

## Phase 1: Diseño y Contratos

### 1. Modelo de Datos

**Estado**: ✅ COMPLETADO - Ver [data-model.md](data-model.md)

**Entidades Principales**:

- **Usuario**: email, password_hash, nombre, rol, created_at, last_login
- **PerfilCargo**: titulo, descripcion, puntos_fuertes (JSON), **umbral_recomendado**, **umbral_reservas**, created_by
- **CV**: file_name, file_type, file_size, uploaded_by, status, extracted_text, error_message
- **Analisis**: cv_id, perfil_id, puntaje, etiqueta, feedback, analyzed_by
- **PortalCredential**: portal_name, cliente_id, usuario, encrypted_secret

**Nuevos Campos por Clarificaciones**:
- `PerfilCargo.umbral_recomendado` (int, default 70)
- `PerfilCargo.umbral_reservas` (int, default 40)

### 2. Contratos de API

**Estado**: ✅ COMPLETADO - Ver [contracts/api.md](contracts/api.md)

**Endpoints Principales**:

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | /api/auth/login | Autenticación email/password |
| POST | /api/auth/logout | Cerrar sesión |
| POST | /api/auth/recover | Solicitar recuperación |
| POST | /api/auth/reset | Resetear con token |
| POST | /api/cvs/upload | Upload múltiple (multipart) |
| GET | /api/cvs/{id}/analysis | Obtener análisis |
| POST | /api/profiles | Crear perfil (con umbrales) |
| POST | /api/analysis/batch | Disparar análisis masivo |
| GET | /api/history/export | Exportar XLSX corporativo |
| PUT | /api/portals/{name}/credentials | Configurar portal |

### 3. Guía Rápida

**Estado**: ✅ COMPLETADO - Ver [quickstart.md](quickstart.md)

**Comandos Esenciales**:

```bash
# Instalar dependencias
pip install -e ".[dev]"

# Inicializar DB
python scripts/migrate.py upgrade

# Crear admin
python scripts/create_admin.py

# Iniciar servidor
uvicorn backend.src.main:app --reload

# Compilar CSS (watch mode)
./tailwindcss -i ./backend/src/static/css/input.css -o ./backend/src/static/css/styles.css --watch
```

### 4. Actualización de Contexto de Agente

**Estado**: ✅ COMPLETADO - Ver [QWEN.md](../../../QWEN.md)

El archivo `QWEN.md` ya referencia este plan:
```markdown
<!-- SPECKIT START -->
Para contexto adicional sobre tecnologías, estructura del proyecto,
comandos shell y otra información importante, lee el plan actual:
`specs/001-ai-recruiter-pro/plan.md`
<!-- SPECKIT END -->
```

## Phase 2: Desglose de Tareas

**Siguiente Comando**: `/speckit.tasks`

Este comando generará `tasks.md` con tareas individuales derivadas de:
- Historias de Usuario (5 historias priorizadas)
- Requisitos Funcionales (21 requisitos)
- Entidades de datos (5 modelos)
- Endpoints de API (10+ endpoints)
- Componentes UI (sidebar, upload zone, progress bars, tables, badges)

**Estimación de Tareas**: ~25-35 tareas agrupadas por módulo

## Dependencias Externas

| Dependencia | Propósito | Estado |
|-------------|-----------|--------|
| **Deepseek API** | Proveedor IA inicial (económico) | Pendiente configuración |
| **sentence-transformers** | Embeddings multilingües | Lista (pip) |
| **pdfplumber** | Extracción texto PDF | Lista (pip) |
| **python-docx** | Extracción texto DOCX | Lista (pip) |
| **openpyxl** | Exportación XLSX | Lista (pip) |
| **Fernet (cryptography)** | Encriptación credenciales | Lista (pip) |

## Criterios de Aceptación del Plan

- [x] Contexto técnico completo y sin ambigüedades
- [x] Estructura de proyecto definida con paths reales
- [x] Modelo de datos alineado con especificación y clarificaciones
- [x] Contratos de API documentados
- [x] Dependencies externas identificadas
- [x] Contexto de agente actualizado en QWEN.md
- [ ] Tareas desglosadas (pendiente /speckit.tasks)

## Próximos Pasos

1. **Ejecutar `/speckit.tasks`**: Generar lista de tareas priorizadas
2. **Comenzar implementación**: Seguir tareas en orden (P1 → P5)
3. **Configurar Deepseek**: Obtener API key y configurar en .env
4. **Tests unitarios**: Crear tests para cada service antes de implementación

---

**Estado del Plan**: ✅ COMPLETADO - Listo para /speckit.tasks
**Artefactos Generados**: plan.md (este archivo)
**Artefactos Existentes**: spec.md, data-model.md, quickstart.md, contracts/api.md
**Siguiente**: `/speckit.tasks`

# AI-Recruiter Pro

Sistema inteligente de análisis de CVs con IA para reclutamiento de personal.

## 🚀 Características Principales

- **Análisis Masivo de CVs**: Carga y analiza múltiples CVs simultáneamente (PDF, DOCX, TXT)
- **Matching Inteligente**: Compara CVs contra perfiles de cargo usando IA (GROQ/Deepseek)
- **Layered Scoring**: Evaluación dimensional (técnico, experiencia, soft skills) con penalizaciones
- **Histórico de Análisis**: Filtrado, exportación a Excel y seguimiento de candidatos
- **Gestión de Usuarios**: Roles (Admin/Reclutador), sesiones y recuperación de contraseña
- **Exportación XLSX**: Reportes con formato corporativo y colores condicionales

## 📋 Requisitos

- **Python**: 3.11 o superior
- **Node.js**: Para compilar Tailwind CSS (opcional, solo desarrollo)
- **Base de Datos**: SQLite (producción: PostgreSQL/MySQL)

## 🛠️ Instalación

### 1. Clonar repositorio

```bash
cd C:\Users\hp\Desktop\PROYECTOS\analizer_beta_2
```

### 2. Instalar dependencias de Python

```bash
pip install -e ".[dev]"
```

### 3. Instalar Tailwind CSS (opcional, solo si modificas estilos)

```bash
npm install -g tailwindcss@latest
```

## ⚙️ Configuración

### 1. Copiar archivo de entorno

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Linux/Mac
cp .env.example .env
```

### 2. Editar `.env` con tus credenciales

```ini
# Clave secreta para sesiones y tokens (generar con: openssl rand -hex 32)
SECRET_KEY=tu_clave_secreta_muy_larga_y_segura_aqui

# API Key de GROQ para análisis con IA (obtener en https://console.groq.com)
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# URL de base de datos (SQLite para desarrollo)
DATABASE_URL=sqlite:///./analizer.db

# Clave para encriptar credenciales de portales (opcional)
CREDENTIAL_ENCRYPTION_KEY=tu_clave_de_encriptacion_aqui

# Versión de la aplicación
VERSION=0.1.0
```

### 3. Generar clave secreta (recomendado)

```bash
# Python
python -c "import secrets; print(secrets.token_hex(32))"

# Linux/Mac
openssl rand -hex 32
```

## 🗄️ Migraciones

Inicializar la base de datos y crear tablas:

```bash
cd backend/src
python scripts/migrate.py upgrade
```

### Crear usuario administrador

```bash
cd backend/src
python scripts/create_admin.py
```

**Credenciales por defecto**:
- Email: `admin@test.com`
- Password: `admin123`

**⚠️ Importante**: Cambiar la contraseña después del primer login.

## ▶️ Ejecución

### Iniciar servidor de desarrollo

```bash
cd backend/src
python -m uvicorn main:app --reload --port 8000
```

### Opciones adicionales

```bash
# Producción (sin auto-reload)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# Puerto personalizado
python -m uvicorn main:app --reload --port 8001

# Con logging detallado
PYTHONPATH=backend/src uvicorn main:app --reload --log-level debug
```

### Verificar que está corriendo

Abrir navegador en: http://localhost:8000

O verificar health check:

```bash
curl http://localhost:8000/health
# Respuesta: {"status":"healthy","version":"0.1.0"}
```

## 📖 Uso Básico

### 1. Login

1. Navegar a http://localhost:8000/login
2. Ingresar credenciales (email y password)
3. Click en "Iniciar Sesión"

### 2. Crear Perfil de Cargo

1. Ir a "Perfiles" en el sidebar
2. Click en "Nuevo Perfil"
3. Completar formulario:
   - Título del cargo
   - Descripción
   - Habilidades requeridas (separadas por comas)
   - Habilidades deseables
   - Nivel de experiencia (junior/mid/senior)
   - Rango salarial
   - Departamento
4. Click en "Guardar"

### 3. Cargar CVs

1. Ir a "Inicio" en el sidebar
2. Arrastrar archivos PDF/DOCX/TXT a la zona de upload
3. O hacer click para seleccionar archivos
4. Esperar a que se procesen (barra de progreso)

### 4. Analizar CVs

1. En "Inicio", seleccionar CVs de la lista (checkboxes)
2. Seleccionar perfil de cargo del dropdown
3. Click en "Analizar CVs"
4. Esperar análisis (puede tardar 30-60 segundos por CV)
5. Ver resultados con puntaje, etiqueta y feedback

### 5. Ver Histórico

1. Ir a "Histórico" en el sidebar
2. Filtrar por:
   - Perfil de cargo
   - Fecha desde/hasta
   - Puntaje mínimo/máximo
   - Etiqueta (Recomendado/Reservas/No Recomendado)
   - Búsqueda por nombre
3. Exportar a Excel si es necesario

## 🧪 Testing

### Ejecutar tests unitarios

```bash
cd backend
python -m pytest tests/unit/ -v
```

### Ejecutar tests de integración

```bash
python -m pytest tests/integration/ -v
```

### Ejecutar todos los tests

```bash
python -m pytest tests/ -v --tb=short
```

### Cobertura de tests

```bash
python -m pytest tests/ --cov=src --cov-report=html
# Abrir: htmlcov/index.html
```

## 📁 Estructura del Proyecto

```
analizer_beta_2/
├── backend/
│   ├── src/
│   │   ├── api/
│   │   │   ├── routes/       # Endpoints de API
│   │   │   ├── middleware/   # Auth middleware
│   │   │   └── deps.py       # Dependencias (get_db, require_auth)
│   │   ├── core/
│   │   │   ├── config.py     # Configuración y settings
│   │   │   ├── database.py   # Conexión DB
│   │   │   └── security.py   # Hash passwords, encriptación
│   │   ├── models/           # Modelos SQLAlchemy
│   │   ├── services/         # Lógica de negocio
│   │   │   └── ia_analyzer/  # Adapters de IA (GROQ, Deepseek, Local)
│   │   ├── templates/        # Templates Jinja2/HTMX
│   │   ├── static/           # CSS, JS, imágenes
│   │   └── main.py           # Aplicación FastAPI
│   ├── tests/
│   │   ├── unit/             # Tests unitarios
│   │   ├── integration/      # Tests de integración
│   │   └── contract/         # Tests de contrato de API
│   ├── scripts/
│   │   ├── migrate.py        # Migraciones de DB
│   │   └── create_admin.py   # Crear admin
│   └── uploads/              # CVs subidos
├── specs/
│   └── 001-ai-recruiter-pro/
│       ├── tasks.md          # Tareas del proyecto
│       └── spec.md           # Especificación técnica
├── .env                      # Variables de entorno (NO COMMIT)
├── .env.example              # Ejemplo de .env
├── pyproject.toml            # Dependencias y configuración
└── README.md                 # Este archivo
```

## 🔧 Troubleshooting

### Error: "GROQ_API_KEY no configurada"

**Solución**: Verificar que `.env` tenga la variable:

```ini
GROQ_API_KEY=gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

Reiniciar el servidor después de agregar.

### Error: "UNIQUE constraint failed: analisis.cv_id"

**Solución**: La tabla fue creada antes del fix. Recrear:

```bash
cd backend/src
python -c "from core.database import engine; from sqlalchemy import text; engine.execute(text('DROP TABLE IF EXISTS analisis'))"
python scripts/migrate.py upgrade
```

### Error: "ModuleNotFoundError: No module named 'src'"

**Causa**: Estás ejecutando desde el directorio incorrecto.

**Solución**:

```bash
cd backend/src
python -m uvicorn main:app --reload
```

### Los CVs no se analizan (se queda "Analizando...")

**Posibles causas**:

1. **Sin sesión activa**: Iniciar sesión primero
2. **GROQ_API_KEY inválida**: Verificar en https://console.groq.com
3. **CV sin texto extraído**: Reintentar upload del CV

**Debug**: Revisar logs del servidor en consola.

### Error: "No autenticado" al llamar API

**Solución**: Los endpoints de API requieren autenticación.

- Para HTMX: El middleware maneja la sesión automáticamente
- Para fetch API: Incluir cookie `session_id` en los headers

## 📊 Estado del Proyecto

| Métrica | Valor |
|---------|-------|
| **Progreso Total** | 91% (106/117 tareas) |
| **MVP** | ✅ Completo |
| **Tests** | ✅ 51 tests unitarios passing |
| **Documentación** | ✅ README.md |
| **Producción** | 🔄 En progreso |

### Tareas Pendientes

- [ ] Rate limiting (60 req/min por usuario)
- [ ] CORS para producción
- [ ] Pruebas de carga (50 CVs en <5 min)
- [ ] Pruebas de concurrencia (10 usuarios simultáneos)
- [ ] Seed data para testing

## 📝 Licencia

Este proyecto es propiedad privada. Todos los derechos reservados.

## 📞 Soporte

Para reportar bugs o solicitar soporte, contactar al equipo de desarrollo.

---

**Última actualización**: Mayo 2026  
**Versión**: 0.1.0

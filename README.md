# CV Analyzer

Aplicación web para revisar CVs de forma masiva: sube los archivos, los evalúa con IA contra un perfil de cargo y devuelve un ranking con puntaje, etiqueta y feedback por candidato.

> Se levanta con Docker en dos comandos y funciona sin API key (análisis local). Ver [Arranque rápido](#arranque-rápido-con-docker).

## Qué hace

- **Autenticación con sesiones** (cookie HttpOnly) y roles (`admin` / `analista`).
- **Perfiles de cargo**: skills requeridas y deseables, seniority, rango salarial y pesos de evaluación configurables.
- **Carga masiva de CVs** en PDF, DOCX y TXT (hasta 10 MB por archivo, 50 por lote).
- **Extracción de datos** del CV: contacto, experiencia, educación, habilidades e idiomas.
- **Análisis con IA**: Groq como proveedor principal y un analizador local heurístico como fallback si no hay API key.
- **Ranking y etiquetas**: `Recomendado`, `Reservas`, `No Recomendado`, con justificación.
- **Histórico filtrable** por perfil, fecha, puntaje y etiqueta, con exportación a Excel.
- **Tests** unitarios, de integración y de contrato en `backend/tests`.

## Stack

| Capa | Tecnología |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy 2 |
| Base de datos | SQLite (dev) / PostgreSQL (producción) |
| Frontend | Jinja2 + HTMX + Tailwind CSS |
| IA | Groq (opcional), DeepSeek (opcional), fallback local |
| Deploy | Docker / Render |

## Arranque rápido con Docker

```bash
git clone https://github.com/gonesteband-ops/CV_Analyzer.git
cd CV_Analyzer
cp .env.example .env          # PowerShell: Copy-Item .env.example .env
```

Edita `.env` y completa al menos:

```ini
SECRET_KEY=una-clave-larga-y-aleatoria
CREDENTIAL_ENCRYPTION_KEY=<clave Fernet, ver abajo>
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=UnaClaveSegura123
```

`CREDENTIAL_ENCRYPTION_KEY` debe ser una clave Fernet válida. Genérala con:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Luego:

```bash
docker compose up --build
```

Abre `http://localhost:8001/login` e ingresa con el `ADMIN_EMAIL` / `ADMIN_PASSWORD` que definiste. El usuario se crea automáticamente al iniciar.

## Arranque local (sin Docker)

Requiere Python 3.11+.

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux / macOS
source .venv/bin/activate

pip install -r requirements.txt
cp .env.example .env          # completar SECRET_KEY y CREDENTIAL_ENCRYPTION_KEY

cd backend/src
python -m uvicorn main:app --reload --port 8000
```

Verificar: `curl http://localhost:8000/health` → `{"status":"healthy","version":"0.1.0"}`.

### Variables de entorno

| Variable | Obligatoria | Uso |
|---|---|---|
| `SECRET_KEY` | Sí | Firma de sesiones |
| `CREDENTIAL_ENCRYPTION_KEY` | Sí | Cifrado de credenciales de portales |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | No | Crea el admin inicial si no existe |
| `GROQ_API_KEY` | No | Análisis con IA; sin ella se usa el analizador local |
| `DEEPSEEK_API_KEY` | No | Proveedor alternativo de IA |
| `DATABASE_URL` | No | Por defecto SQLite |
| `DB_PATH` | No | Fuerza la ruta del archivo SQLite (Docker usa `/app/data/analizer.db`) |

## Uso

1. Inicia sesión en `/login`.
2. Crea un perfil de cargo en `/perfiles`.
3. Sube uno o más CVs desde el inicio.
4. Selecciona los CVs y el perfil, y ejecuta el análisis.
5. Revisa resultados y ranking en `/historico`; exporta a Excel si lo necesitas.

## Endpoints principales

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/docs` | Documentación OpenAPI |
| POST | `/api/auth/login` | Inicio de sesión |
| POST | `/api/cvs/upload` | Carga de CVs |
| POST | `/api/cvs/analysis/batch` | Análisis por lote |
| GET | `/api/cvs/list` | Listado de CVs |
| GET/POST | `/api/profiles` | Perfiles de cargo |
| GET | `/api/history` | Histórico de análisis |
| GET | `/api/history/export` | Exportación a Excel |

## Tests

```bash
cd backend
python -m pytest tests -q
```

## Estructura

```
CV_Analyzer/
├── backend/
│   ├── src/
│   │   ├── api/            # Rutas, middleware y dependencias
│   │   ├── core/           # Configuración, DB y seguridad
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── services/       # Extracción de CVs, matching y adapters de IA
│   │   ├── templates/      # Vistas Jinja2/HTMX
│   │   ├── static/         # CSS, JS e imágenes
│   │   ├── main.py         # Aplicación FastAPI
│   │   └── init_db_admin.py
│   ├── tests/              # unit / integration / contract
│   └── scripts/            # Scripts de carga y mantenimiento
├── scripts/                # create_admin.py, migrate.py
├── specs/                  # Especificaciones del proyecto
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Notas de seguridad

- Las claves se leen solo desde `.env` o variables de entorno; no hay credenciales en el código.
- `.env`, bases SQLite, CVs reales y cookies están excluidos por `.gitignore`.
- En producción usa `DEBUG=False`, `SESSION_COOKIE_SECURE=True` y HTTPS.

## Licencia

Código compartido con fines de portafolio y evaluación técnica.

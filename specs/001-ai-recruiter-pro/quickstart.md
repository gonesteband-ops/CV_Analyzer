# Quickstart Guide: AI-Recruiter Pro

**Feature**: 001-ai-recruiter-pro | **Date**: 2026-04-23
**Purpose**: Get developers up and running quickly

## Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git
- (Optional) PostgreSQL for production-like testing

## Development Setup (5 minutes)

### 1. Clone and Environment

```bash
# Clone repository
cd C:\Users\hp\Desktop\PROYECTOS\analizer_beta_2

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Windows (CMD):
venv\Scripts\activate.bat
# Linux/Mac:
source venv/bin/activate
```

### 2. Install Dependencies

```bash
# Install with development dependencies
pip install -e ".[dev]"

# Verify installation
pytest --version  # Should show pytest version
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and set:
# SECRET_KEY=your-secret-key-here  # Run: python -c "import secrets; print(secrets.token_urlsafe(32))"
# DATABASE_URL=sqlite:///./dev.db
# CREDENTIAL_ENCRYPTION_KEY=your-encryption-key  # Run: from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())
```

**.env.example** (create this file):
```bash
# Application
SECRET_KEY=change-me-in-production
DEBUG=True

# Database
DATABASE_URL=sqlite:///./dev.db

# Encryption
CREDENTIAL_ENCRYPTION_KEY=change-me-in-production

# Timezone
TIMEZONE=America/Santiago
```

### 4. Initialize Database

```bash
# Run migrations
python scripts/migrate.py upgrade

# Create first admin user
python scripts/create_admin.py
# Follow prompts: email, password, nombre
```

### 5. Start Development Server

```bash
# Option A: With hot-reload (recommended, requires Air)
air

# Option B: Direct run
uvicorn backend.src.main:app --reload --host 0.0.0.0 --port 8000

# Access application
# Open browser: http://localhost:8000
# Login with admin credentials created in step 4
```

### 6. Build Tailwind CSS (Development)

```bash
# Download Tailwind CLI standalone (one-time)
curl -sLO https://github.com/tailwindlabs/tailwindcss/releases/latest/download/tailwindcss-windows-x64.exe
mv tailwindcss-windows-x64.exe tailwindcss.exe

# Build CSS with watch mode
./tailwindcss.exe -i ./backend/static/css/input.css -o ./backend/static/css/styles.css --watch
```

**Note**: If using Air for hot-reload, configure it to also watch for Tailwind rebuilds.

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend.src --cov-report=html

# Run specific test file
pytest backend/tests/unit/test_cv_parser.py -v

# Run integration tests (requires test database)
pytest backend/tests/integration/ -v

# View coverage report
open htmlcov/index.html  # Linux/Mac
start htmlcov\\index.html  # Windows
```

### Test Database Setup

```bash
# Tests use separate test database
# Set in .env.test or pytest fixture
DATABASE_URL=sqlite:///./test.db
```

## Project Structure Overview

```
analizer_beta_2/
├── backend/
│   ├── src/
│   │   ├── api/          # FastAPI routes
│   │   ├── models/       # SQLAlchemy models
│   │   ├── services/     # Business logic
│   │   ├── core/         # Config, security, database
│   │   ├── templates/    # Jinja2 HTML templates
│   │   └── main.py       # FastAPI app entry point
│   ├── static/
│   │   ├── css/          # Compiled Tailwind CSS
│   │   └── js/           # HTMX configuration
│   └── tests/
│       ├── unit/         # Unit tests
│       ├── integration/  # Integration tests
│       └── contract/     # API contract tests
├── scripts/
│   ├── migrate.py        # Database migrations
│   ├── create_admin.py   # Admin user creation
│   └── dev.sh            # Development startup
├── specs/
│   └── 001-ai-recruiter-pro/  # Feature documentation
└── .env                  # Environment configuration
```

## Common Tasks

### Create a New User

```bash
python scripts/create_user.py
# Prompts: email, password, nombre, rol (reclutador/administrador)
```

### Reset Password Manually

```bash
python scripts/reset_password.py user@email.com
# Generates temporary password
```

### Export Sample Data

```bash
python scripts/export_sample.py --output sample_data.xlsx
```

### Database Operations

```bash
# Check migration status
python scripts/migrate.py current

# Rollback last migration
python scripts/migrate.py downgrade -1

# Create new migration (after model changes)
alembic -c backend/src/alembic.ini revision --autogenerate -m "Description"
```

## Debugging

### Enable Debug Logging

```bash
# In .env, set:
LOG_LEVEL=DEBUG
```

### Access API Documentation

```bash
# Swagger UI (interactive API docs)
http://localhost:8000/docs

# ReDoc (alternative API docs)
http://localhost:8000/redoc

# OpenAPI JSON
http://localhost:8000/openapi.json
```

### HTMX Debugging

Add to templates for debug mode:

```html
<script src="https://unpkg.com/htmx.org/dist/ext/debug.js"></script>
```

Check network tab in browser DevTools for HTMX requests.

## Production Deployment

### Environment Variables

```bash
# Production .env
SECRET_KEY=<strong-random-key>
DEBUG=False
DATABASE_URL=postgresql://user:password@localhost:5432/ai_recruiter
CREDENTIAL_ENCRYPTION_KEY=<strong-random-key>
TIMEZONE=America/Santiago
```

### Database Migration

```bash
# Ensure PostgreSQL is running
# Update DATABASE_URL in .env
python scripts/migrate.py upgrade
```

### Run with Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn backend.src.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### HTTPS Configuration

Deploy behind reverse proxy (nginx, Apache) with Let's Encrypt SSL.

**nginx example**:
```nginx
server {
    listen 80;
    server_name ai-recruiter.yourdomain.cl;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name ai-recruiter.yourdomain.cl;

    ssl_certificate /etc/letsencrypt/live/ai-recruiter.yourdomain.cl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/ai-recruiter.yourdomain.cl/privkey.pem;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Troubleshooting

### "Module not found" errors

```bash
# Ensure virtual environment is activated
# Reinstall dependencies
pip install -e ".[dev]"
```

### Database migration fails

```bash
# Check current migration status
python scripts/migrate.py current

# If corrupted, reset (WARNING: deletes data)
rm dev.db
python scripts/migrate.py upgrade
```

### HTMX requests not working

- Check browser console for JavaScript errors
- Verify HTMX script is loaded in base template
- Check network tab for 401/403 errors (authentication issues)

### Tailwind styles not applying

```bash
# Rebuild CSS
./tailwindcss.exe -i ./backend/static/css/input.css -o ./backend/static/css/styles.css

# Check tailwind.config.js content paths match template locations
```

### Tests failing

```bash
# Clear pytest cache
pytest --cache-clear

# Run with verbose output
pytest -vvv --tb=long
```

## Next Steps

After setup, proceed to:

1. **Read API Contracts**: See `contracts/` directory for endpoint specifications
2. **Review Data Model**: See `data-model.md` for entity details
3. **Start Development**: Pick a task from `tasks.md` (created by `/speckit.tasks`)

## Support

For issues or questions:

- Check existing issues in repository
- Review `research.md` for architectural decisions
- Consult FastAPI, HTMX, Tailwind CSS documentation

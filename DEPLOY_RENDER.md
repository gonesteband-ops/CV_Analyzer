# Despliegue en Render

## Archivos Docker incluidos

- `Dockerfile` - Configuración de la imagen Python 3.11
- `docker-compose.yml` - Orquestación local (para testing)
- `.dockerignore` - Excluye archivos de desarrollo del build
- `backend/requirements.txt` - Dependencias congeladas

## Pasos para desplegar en Render

### 1. Conectar repositorio a Render

1. Ir a https://dashboard.render.com
2. Click en **"New +"** → **"Web Service"**
3. Conectar repositorio de GitHub
4. Seleccionar el repositorio `analizer_beta_2`

### 2. Configurar el Web Service

**Configuración básica:**
- **Name**: `ai-recruiter-pro`
- **Region**: `Oregon (USA)` o la más cercana a Chile
- **Branch**: `main` (o tu rama principal)
- **Root Directory**: (dejar vacío)
- **Runtime**: `Python 3`
- **Build Command**: `pip install -r backend/requirements.txt`
- **Start Command**: `cd backend/src && uvicorn src.main:app --host 0.0.0.0 --port 8000`

**Variables de entorno:**
```bash
SECRET_KEY=tu-secret-key-generada-aqui
DEBUG=False
DATABASE_URL=sqlite:///./analizer.db
TIMEZONE=America/Santiago
SESSION_COOKIE_NAME=session_id
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=lax
```

**Plan:**
- **Free** (para testing) o **Standard** ($7/mes para producción)

### 3. Crear usuario administrador (POST-DEPLOY)

Después del primer deploy, la base de datos estará vacía. Sigue estos pasos:

#### Opción A: Usando la Shell de Render (RECOMENDADO)

1. Ir al dashboard del Web Service en Render
2. Click en el botón **"Shell"** (arriba a la derecha)
3. En la terminal que se abre, ejecutar:

```bash
cd backend/src && python init_db_admin.py
```

4. Verás la salida:
```
[*] Iniciando creacion de usuario administrador...
    Database: sqlite:///./analizer.db
[*] Inicializando base de datos...
[+] Base de datos inicializada correctamente
[+] Usuario administrador creado exitosamente!
    ID: 1
    Email: admin@test.com
    Nombre: Admin
    Rol: admin

[CREDENCIALES]
    Email: admin@test.com
    Password: admin123

[!] IMPORTANTE! Cambia la contraseña despues del primer login
```

5. Ir a `https://ai-recruiter-pro.onrender.com/login`
6. Iniciar sesión con: `admin@test.com` / `admin123`

#### Opción B: Script manual desde Shell

Si prefieres no usar el script, ejecuta directamente en la Shell:

```bash
cd backend/src && python -c "
from core.database import SessionLocal
from models.usuario import Usuario
from datetime import datetime
from core.security import hash_password

db = SessionLocal()
admin = Usuario(
    email='admin@test.com',
    nombre='Administrador',
    password_hash=hash_password('admin123'),
    rol='admin',
    created_at=datetime.utcnow()
)
db.add(admin)
db.commit()
db.close()
print('Admin creado: admin@test.com / admin123')
"
```

### 4. Verificar despliegue

**Health check:**
```bash
curl https://ai-recruiter-pro.onrender.com/health
```

**Login:**
```bash
curl https://ai-recruiter-pro.onrender.com/login
```

**Ver logs:**
- Ir al dashboard del Web Service
- Click en **"Logs"**
- Ver logs en tiempo real

## Comandos útiles en Render Shell

```bash
# Ver logs en tiempo real
tail -f /opt/render/project/src/backend/src/logs/app.log

# Reiniciar la aplicación
render-cli restart

# Ver variables de entorno
env | grep -E 'SECRET|DATABASE|SESSION'

# Explorar la base de datos
cd backend/src && python -c "from core.database import SessionLocal; db = SessionLocal(); print(db.query(models.Usuario).all())"

# Ver uploads
ls -la /opt/render/project/src/backend/src/uploads/
```

## Consideraciones de producción

### Seguridad
- ✅ `DEBUG=False` en producción
- ✅ `SESSION_COOKIE_SECURE=True` (requiere HTTPS)
- ✅ `SECRET_KEY` única y segura (generar con `openssl rand -hex 32`)
- ✅ Cambiar contraseña de admin después del primer login

### Base de datos
- SQLite es suficiente para testing y bajo tráfico
- Para producción con alto tráfico, migrar a PostgreSQL:
  - Add PostgreSQL en Render dashboard
  - Actualizar `DATABASE_URL` en variables de entorno
  - Re-deploy automático

### Uploads
- Los CVs se guardan en `/opt/render/project/src/backend/src/uploads/`
- Se persisten automáticamente (Render mantiene el filesystem)
- Límite: 10GB en plan Free, 50GB en Standard

### Cold starts (plan Free)
- El plan Free tiene cold start de ~30 segundos
- Primer request después de 15 min de inactividad será lento
- Considerar plan Standard para producción

## Solución de problemas

### Error: "ModuleNotFoundError: No module named 'src.main'"
- Verificar que el Start Command sea: `cd backend/src && uvicorn src.main:app --host 0.0.0.0 --port 8000`

### Error: "DATABASE_URL no configurada"
- Verificar variables de entorno en Render dashboard
- Asegurar que `DATABASE_URL=sqlite:///./analizer.db`

### Error: "No hay usuarios creados"
- Ejecutar `init_db_admin.py` desde la Shell
- Verificar que el script se incluyó en el build (revisar `.dockerignore`)

### Error: "Cannot write to uploads"
- Verificar permisos en Dockerfile: `RUN mkdir -p /app/src/uploads && chmod 777 /app/src/uploads`

## Próximos pasos

1. ✅ Desplegar en Render
2. ✅ Crear usuario admin
3. ✅ Cambiar contraseña de admin
4. ✅ Configurar dominio personalizado (opcional)
5. ✅ Habilitar HTTPS automático (Render lo hace por defecto)
6. ✅ Configurar backups de la base de datos (manual en SQLite)
7. ✅ Monitorear logs y métricas

---

**Documentación actualizada:** Mayo 2026
**Versión:** AI-Recruiter Pro 0.1.0

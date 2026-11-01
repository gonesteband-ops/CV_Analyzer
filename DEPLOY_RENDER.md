# Despliegue en Render

El proyecto ya incluye `Dockerfile`, por lo que Render puede construirlo directamente.

## 1. Crear el servicio

1. En https://dashboard.render.com → **New +** → **Web Service**.
2. Conectar el repositorio `CV_Analyzer`.
3. Configurar:
   - **Runtime**: `Docker`
   - **Branch**: `main`
   - **Root Directory**: vacío
   - **Plan**: Free o Standard

## 2. Variables de entorno

| Variable | Valor |
|---|---|
| `SECRET_KEY` | Clave aleatoria larga (`openssl rand -hex 32`) |
| `CREDENTIAL_ENCRYPTION_KEY` | Otra clave aleatoria larga |
| `DEBUG` | `False` |
| `SESSION_COOKIE_SECURE` | `True` |
| `ADMIN_EMAIL` | Email del administrador |
| `ADMIN_PASSWORD` | Password del administrador |
| `GROQ_API_KEY` | Opcional (sin ella se usa el analizador local) |
| `DB_PATH` | `/app/data/analizer.db` |

El administrador se crea automáticamente en el primer arranque si defines `ADMIN_EMAIL` y `ADMIN_PASSWORD`. No necesitas Shell.

## 3. Persistencia

Render no conserva el filesystem entre deploys. Para no perder la base SQLite ni los uploads, agrega un **Persistent Disk**:

- Mount Path: `/app/data`
- Size: 1 GB (suficiente para una demo)

El `Dockerfile` ya expone el puerto con `${PORT:-8000}`, que es lo que Render espera.

## 4. Verificar

```bash
curl https://TU-SERVICIO.onrender.com/health
```

Debe responder `{"status":"healthy","version":"0.1.0"}`. Luego entra a `/login` con las credenciales configuradas.

## Notas

- El plan Free duerme tras 15 minutos de inactividad; el primer request puede tardar ~30 segundos.
- Para alto tráfico, migra a PostgreSQL cambiando `DATABASE_URL`.
- Cambia la contraseña del administrador después del primer login.

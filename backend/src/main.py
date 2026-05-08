import logging
import uuid
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, File, Request, UploadFile, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy.orm import Session
from passlib.context import CryptContext

# Imports de tu app
from core.config import settings
from core.database import SessionLocal, engine, get_db, init_db
from api.deps import require_auth
from models.usuario import Usuario
import models.usuario as models_module
from models.cv import CV
from models.analisis import Analisis

# 1. CONFIGURACIÓN INICIAL
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
BASE_DIR = Path(__file__).parent

# 2. CREAR APLICACIÓN (Única instancia)
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="Sistema de automatización de revisión masiva de CVs para call centers",
)

# 3. EVENTO DE INICIO UNIFICADO (Tablas + Admin + Logs)
@app.on_event("startup")
async def startup_event():
    # Inicializa tablas
    models_module.Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        admin_email = "gonzalo@iarecruiter.cl"
        user = db.query(Usuario).filter(Usuario.email == admin_email).first()

        if not user:
            nuevo = Usuario(
                nombre="Gonzalo",
                email=admin_email,
                password_hash=pwd_context.hash("Admin.123"),
                rol="admin",
                created_at=datetime.now()
            )
            db.add(nuevo)
            db.commit()
            print(f" USUARIO CREADO: {admin_email}")
        else:
            user.password_hash = pwd_context.hash("Admin.123")
            db.commit()
            print(f" CREDENCIALES ACTUALIZADAS: {admin_email}")

    except Exception as e:
        print(f" ERROR EN STARTUP: {e}")
    finally:
        db.close()

    logger.info(f"{settings.app_name} v{settings.version} iniciada")

# 4. MIDDLEWARES
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from api.middleware.auth import AuthMiddleware
app.add_middleware(AuthMiddleware)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"REQ: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"RES: {request.method} {request.url.path} - {response.status_code}")
    return response

# 5. ESTATICOS Y TEMPLATES
templates = Jinja2Templates(directory=BASE_DIR / "templates")
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Filtros personalizados
def format_currency(v):
    """Formatea un número como moneda."""
    if v is None:
        return ""
    try:
        return f"${int(v):,}".replace(",", ".")
    except (ValueError, TypeError):
        return ""

templates.env.filters["currency"] = format_currency

# 6. MANEJO DE ERRORES
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Error en {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Error interno del servidor"}
    )

# 7. RUTAS DE PÁGINAS
@app.get("/")
async def root(request: Request, db: Session = Depends(get_db)):
    usuario = getattr(request.state, "usuario", None)
    cvs, analisis_dict = [], {}
    if usuario:
        cvs = db.query(CV).filter(CV.uploaded_by == usuario.id).order_by(CV.uploaded_at.desc()).all()
        if cvs:
            cv_ids = [cv.id for cv in cvs]
            analisis_list = db.query(Analisis).filter(Analisis.cv_id.in_(cv_ids)).all()
            analisis_dict = {a.cv_id: a for a in analisis_list}
    return templates.TemplateResponse("pages/home.html", {"request": request, "usuario": usuario, "cvs": cvs, "analisis_dict": analisis_dict, "show_sidebar": True})

@app.get("/login")
async def login_page(request: Request):
    return templates.TemplateResponse("pages/login.html", {"request": request})

@app.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/login")
    response.delete_cookie(key="session_id")
    return response


# ============================================
# RUTAS DE PÁGINAS (requieren autenticación)
# ============================================

@app.get("/perfiles")
async def perfiles_page(request: Request, db: Session = Depends(get_db)):
    """Página de gestión de perfiles de cargo."""
    usuario = getattr(request.state, "usuario", None)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("pages/perfiles.html", {"request": request, "usuario": usuario, "show_sidebar": True})


@app.get("/historico")
async def historico_page(request: Request, db: Session = Depends(get_db)):
    """Página de histórico de análisis."""
    usuario = getattr(request.state, "usuario", None)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("pages/historico.html", {"request": request, "usuario": usuario, "show_sidebar": True})


@app.get("/acerca")
async def acerca_page(request: Request, db: Session = Depends(get_db)):
    """Página de acerca de."""
    usuario = getattr(request.state, "usuario", None)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("pages/acerca_de.html", {"request": request, "usuario": usuario, "show_sidebar": True})


@app.get("/admin/usuarios")
async def admin_usuarios_page(request: Request, db: Session = Depends(get_db)):
    """Página de administración de usuarios (solo admin)."""
    usuario = getattr(request.state, "usuario", None)
    if not usuario:
        return RedirectResponse(url="/login")
    if usuario.rol != "admin":
        return RedirectResponse(url="/")
    return templates.TemplateResponse("pages/admin_usuarios.html", {"request": request, "usuario": usuario, "show_sidebar": True})


@app.get("/portales")
async def portales_page(request: Request, db: Session = Depends(get_db)):
    """Página placeholder de portales de empleo (US4 postergada)."""
    usuario = getattr(request.state, "usuario", None)
    if not usuario:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("pages/portales.html", {"request": request, "usuario": usuario, "show_sidebar": True})


# 8. REGISTRO DE ROUTERS
from api.routes import auth, candidates, cvs, profiles, users
from api.routes.history import router as history_router

# Los routers ya tienen prefijos definidos internamente, no agregar prefijos adicionales
app.include_router(auth.router, tags=["Autenticación"])
app.include_router(candidates.router, tags=["Candidatos"])
app.include_router(cvs.router, tags=["CVs"])
app.include_router(profiles.router, tags=["Perfiles"])
app.include_router(users.router, tags=["Usuarios"])
app.include_router(history_router, tags=["Histórico"])

@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": settings.version}


# 9. BLOQUE DE INICIO DIRECTO (python main.py)
if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print(" AI-Recruiter Pro - Servidor de Desarrollo")
    print("=" * 60)
    print(" URL: http://localhost:8000")
    print(" Login: http://localhost:8000/login")
    print(" Admin: gonzalo@iarecruiter.cl / Admin.123")
    print("=" * 60)
    uvicorn.run(app, host="0.0.0.0", port=8000)

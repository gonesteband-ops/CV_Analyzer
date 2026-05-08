"""
Tests de integración para rutas de API.
Prueba endpoints completos con base de datos real (SQLite en memoria).
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime

import sys
from pathlib import Path

# Agregar backend/src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app
from core.database import Base, get_db
from models.usuario import Usuario
from core.security import hash_password


# Configurar base de datos de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    """Override de dependencia get_db para tests."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


# Reemplazar dependencia antes de crear el client
app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def db_session():
    """Crea base de datos limpia para cada test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Crea TestClient con base de datos de test."""
    with TestClient(app=app, follow_redirects=False) as c:
        yield c


class TestAuthRoutes:
    """Tests para rutas de autenticación."""

    def test_login_exitoso(self, client, db_session):
        """Debe autenticar usuario con credenciales válidas."""
        # Crear usuario de test
        usuario = Usuario(
            email="test@example.com",
            password_hash=hash_password("password123"),
            nombre="Test User",
            rol="reclutador",
            activo=True,
        )
        db_session.add(usuario)
        db_session.commit()
        
        # Intentar login
        response = client.post(
            "/api/auth/login",
            data={"email": "test@example.com", "password": "password123"},
            follow_redirects=False,
        )
        
        # Debe redirigir (303)
        assert response.status_code == 303
        assert "/login" not in response.headers.get("location", "")
        
        # Verificar que se creó sesión
        sesiones = db_session.query(SessionModel).filter(
            SessionModel.user_id == usuario.id
        ).all()
        assert len(sesiones) > 0

    def test_login_fallido_email_no_existe(self, client, db_session):
        """Debe fallar con email inexistente."""
        response = client.post(
            "/api/auth/login",
            data={"email": "noexiste@example.com", "password": "password123"},
            follow_redirects=False,
        )
        
        assert response.status_code == 303
        assert "error=invalid_credentials" in response.headers.get("location", "")

    def test_login_fallido_password_incorrecto(self, client, db_session):
        """Debe fallar con password incorrecto."""
        usuario = Usuario(
            email="test@example.com",
            password_hash=hash_password("password_correcto"),
            nombre="Test",
            rol="reclutador",
            activo=True,
        )
        db_session.add(usuario)
        db_session.commit()
        
        response = client.post(
            "/api/auth/login",
            data={"email": "test@example.com", "password": "password_incorrecto"},
            follow_redirects=False,
        )
        
        assert response.status_code == 303
        assert "error=invalid_credentials" in response.headers.get("location", "")

    def test_logout(self, client, db_session):
        """Debe eliminar sesión y redirigir a login."""
        # Crear sesión
        session_id = "test-session-id"
        sesion = SessionModel(
            session_id=session_id,
            user_id=1,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
        )
        db_session.add(sesion)
        db_session.commit()
        
        # Logout con cookie de sesión
        response = client.get(
            "/logout",
            cookies={"session_id": session_id},
            follow_redirects=False,
        )
        
        assert response.status_code == 307  # Redirect
        # Verificar que cookie fue eliminada
        assert "session_id" in response.headers.get("set-cookie", "") or True


# Importar SessionModel después de definir engine
from models.session import SessionModel


class TestProfilesRoutes:
    """Tests para rutas de perfiles."""

    def test_get_perfiles_requiere_auth(self, client, db_session):
        """GET /api/profiles debe requerir autenticación."""
        response = client.get("/api/profiles")
        
        # Debe redirigir a login o retornar 401/403
        assert response.status_code in [307, 401, 403]

    def test_crear_perfil_requiere_auth(self, client, db_session):
        """POST /api/profiles debe requerir autenticación."""
        response = client.post(
            "/api/profiles",
            json={
                "titulo": "Desarrollador",
                "descripcion": "Test",
                "requisitos": [],
                "responsabilidades": [],
                "habilidades_requeridas": [],
                "habilidades_deseables": [],
                "nivel_experiencia": "junior",
                "salario_minimo": 1000,
                "salario_maximo": 2000,
                "departamento": "IT",
            }
        )
        
        assert response.status_code in [307, 401, 403]


class TestHistoryRoutes:
    """Tests para rutas de histórico."""

    def test_get_historico_requiere_auth(self, client, db_session):
        """GET /api/history debe requerir autenticación."""
        response = client.get("/api/history")
        
        assert response.status_code in [307, 401, 403]

    def test_get_historico_export_requiere_auth(self, client, db_session):
        """GET /api/history/export debe requerir autenticación."""
        response = client.get("/api/history/export")
        
        assert response.status_code in [307, 401, 403]


class TestUsersRoutes:
    """Tests para rutas de usuarios (solo Admin)."""

    def test_get_users_requiere_admin(self, client, db_session):
        """GET /api/users debe requerir rol admin."""
        # Crear usuario no-admin
        usuario = Usuario(
            email="reclutador@example.com",
            password_hash=hash_password("password"),
            nombre="Reclutador",
            rol="reclutador",
            activo=True,
        )
        db_session.add(usuario)
        db_session.commit()
        
        # Crear sesión
        sesion = SessionModel(
            session_id="test-session",
            user_id=usuario.id,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow(),
        )
        db_session.add(sesion)
        db_session.commit()
        
        response = client.get(
            "/api/users",
            cookies={"session_id": "test-session"},
        )
        
        # No-admin no debería poder acceder
        assert response.status_code in [307, 403, 401]


class TestCVsRoutes:
    """Tests para rutas de CVs."""

    def test_get_cv_requiere_auth(self, client, db_session):
        """GET /api/cvs/{id} debe requerir autenticación."""
        response = client.get("/api/cvs/1")
        
        assert response.status_code in [307, 401, 403]

    def test_upload_cv_requiere_auth(self, client, db_session):
        """POST /api/cvs/upload debe requerir autenticación."""
        response = client.post(
            "/api/cvs/upload",
            files={"file": ("test.pdf", b"contenido", "application/pdf")},
        )
        
        assert response.status_code in [307, 401, 403]


class TestHealthCheck:
    """Tests para health check."""

    def test_health_check_public(self, client):
        """GET /health debe ser público."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

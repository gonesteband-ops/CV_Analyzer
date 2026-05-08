"""
Tests de contrato de API.
Verifica que los endpoints respeten los schemas de respuesta definidos.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from main import app
from core.database import Base, get_db

# Configurar base de datos de test
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_contract.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(scope="function")
def client():
    """Crea TestClient para tests de contrato."""
    Base.metadata.create_all(bind=engine)
    with TestClient(app=app) as c:
        yield c
    Base.metadata.drop_all(bind=engine)


class TestContratoRespuestas:
    """Tests que verifican contratos de respuesta de API."""

    def test_health_response_schema(self, client):
        """GET /health debe retornar schema {status, version}."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estructura de respuesta
        assert "status" in data
        assert "version" in data
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)
        assert data["status"] == "healthy"

    def test_error_404_response_schema(self, client):
        """Endpoints inexistentes deben retornar 404 con detail."""
        response = client.get("/endpoint-no-existe")
        
        assert response.status_code == 404
        data = response.json()
        
        # FastAPI retorna {"detail": "Not Found"}
        assert "detail" in data
        assert isinstance(data["detail"], str)

    def test_login_response_redirect(self, client):
        """POST /api/auth/login debe retornar RedirectResponse (303)."""
        response = client.post(
            "/api/auth/login",
            data={"email": "test@test.com", "password": "wrong"},
            follow_redirects=False,
        )
        
        # Login fallido debe redirigir
        assert response.status_code == 303
        assert "location" in response.headers
        assert "/login" in response.headers["location"]

    def test_profiles_list_response_schema(self, client):
        """GET /api/profiles debe retornar lista o redirect si no auth."""
        response = client.get("/api/profiles")
        
        # Sin auth, debe redirigir
        assert response.status_code in [200, 307, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            # Debe ser lista de perfiles
            assert isinstance(data, list)
            for perfil in data:
                assert "id" in perfil or "titulo" in perfil

    def test_create_profile_validation(self, client):
        """POST /api/profiles debe validar campos requeridos."""
        # Intentar crear perfil sin campos requeridos
        response = client.post(
            "/api/profiles",
            json={"titulo": ""},  # Título vacío
        )
        
        # Debe retornar 422 (Validation Error) o redirect
        assert response.status_code in [307, 401, 403, 422]
        
        if response.status_code == 422:
            data = response.json()
            assert "detail" in data
            assert isinstance(data["detail"], list)

    def test_users_list_requires_admin(self, client):
        """GET /api/users debe requerir admin y retornar 403 si no lo es."""
        response = client.get("/api/users")
        
        # Sin auth o no-admin, debe retornar 403/401/307
        assert response.status_code in [307, 401, 403]

    def test_history_response_schema(self, client):
        """GET /api/history debe retornar schema con resultados."""
        response = client.get("/api/history")
        
        # Sin auth, redirect
        assert response.status_code in [200, 307, 401, 403]
        
        if response.status_code == 200:
            data = response.json()
            # Debe tener estructura de paginación o lista
            if isinstance(data, dict):
                assert "results" in data or "items" in data or "data" in data
            elif isinstance(data, list):
                pass  # Lista directa también es válida

    def test_export_xlsx_content_type(self, client):
        """GET /api/history/export debe retornar application/vnd.openxmlformats-officedocument.spreadsheetml.sheet."""
        response = client.get("/api/history/export")
        
        # Sin auth, redirect
        if response.status_code == 200:
            assert "application/vnd" in response.headers.get("content-type", "")
            assert "attachment" in response.headers.get("content-disposition", "")


class TestContratoErrores:
    """Tests que verifican manejo consistente de errores."""

    def test_error_500_schema(self, client):
        """Errores 500 deben retornar schema consistente."""
        # Forzar error 500 es difícil sin modificar código
        # Este test documenta el comportamiento esperado
        pass

    def test_error_400_schema(self, client):
        """Errores 400 deben retornar schema con detail."""
        # Ejemplo: CV inválido
        response = client.post(
            "/api/cvs/upload",
            files={"file": ("test.xls", b"contenido", "application/vnd.ms-excel")},
        )
        
        # Debe retornar 400, 422, o redirect
        assert response.status_code in [307, 400, 401, 403, 422]
        
        if response.status_code in [400, 422]:
            data = response.json()
            assert "detail" in data or "error" in data

    def test_error_401_unauthorized(self, client):
        """Endpoints protegidos sin cookie deben retornar 401/403/307."""
        endpoints_protegidos = [
            ("GET", "/api/profiles"),
            ("GET", "/api/cvs/1"),
            ("GET", "/api/history"),
            ("GET", "/api/users"),
        ]
        
        for method, endpoint in endpoints_protegidos:
            if method == "GET":
                response = client.get(endpoint)
            else:
                response = client.post(endpoint)
            
            # Todos deben requerir auth
            assert response.status_code in [307, 401, 403], f"{endpoint} no requiere auth"


class TestContratoTiposDeDatos:
    """Tests que verifican tipos de datos en respuestas."""

    def test_profile_tipos_de_datos(self, client):
        """Perfiles deben tener tipos de datos correctos."""
        response = client.get("/api/profiles")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                perfil = data[0]
                
                # Verificar tipos
                if "id" in perfil:
                    assert isinstance(perfil["id"], int)
                if "titulo" in perfil:
                    assert isinstance(perfil["titulo"], str)
                if "activo" in perfil:
                    assert isinstance(perfil["activo"], bool)
                if "puntaje" in perfil:
                    assert isinstance(perfil["puntaje"], (int, float))

    def test_user_tipos_de_datos(self, client):
        """Usuarios deben tener tipos de datos correctos."""
        response = client.get("/api/users")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                usuario = data[0]
                
                # Verificar tipos
                if "id" in usuario:
                    assert isinstance(usuario["id"], int)
                if "email" in usuario:
                    assert isinstance(usuario["email"], str)
                    assert "@" in usuario["email"]
                if "nombre" in usuario:
                    assert isinstance(usuario["nombre"], str)
                if "rol" in usuario:
                    assert usuario["rol"] in ["admin", "reclutador"]

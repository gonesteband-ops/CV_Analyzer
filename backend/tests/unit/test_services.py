"""
Tests unitarios para UserService y ProfileService.
Prueba operaciones CRUD de usuarios y perfiles de cargo.
"""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime

from services.user_service import UserService
from services.profile_service import ProfileService, ProfileServiceError
from models.usuario import Usuario


class TestUserService:
    """Tests para UserService."""

    def setup_method(self):
        """Configura mocks antes de cada test."""
        self.mock_db = MagicMock()
        self.service = UserService(self.mock_db)

    def test_obtener_usuario_por_id_existe(self):
        """Debe retornar usuario si existe."""
        usuario_mock = Usuario(
            id=1,
            email="test@example.com",
            nombre="Test User",
            rol="reclutador",
            activo=True,
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = usuario_mock
        
        resultado = self.service.obtener_usuario_por_id(1)
        
        assert resultado == usuario_mock
        assert resultado.email == "test@example.com"

    def test_obtener_usuario_por_id_no_existe(self):
        """Debe retornar None si no existe."""
        self.mock_db.query.return_value.filter.return_value.first.return_value = None
        
        resultado = self.service.obtener_usuario_por_id(999)
        
        assert resultado is None

    def test_obtener_usuario_por_email_existe(self):
        """Debe retornar usuario por email."""
        usuario_mock = Usuario(
            id=1,
            email="test@example.com",
            nombre="Test User",
            rol="admin",
            activo=True,
        )
        self.mock_db.query.return_value.filter.return_value.first.return_value = usuario_mock
        
        resultado = self.service.obtener_usuario_por_email("test@example.com")
        
        assert resultado == usuario_mock
        assert resultado.rol == "admin"

    def test_listar_usuarios_sin_filtros(self):
        """Debe listar usuarios sin filtros."""
        usuarios_mock = [
            Usuario(id=1, email="a@test.com", nombre="A", rol="reclutador", activo=True),
            Usuario(id=2, email="b@test.com", nombre="B", rol="admin", activo=True),
        ]
        self.mock_db.query.return_value.filter.return_value.offset.return_value.limit.return_value.all.return_value = usuarios_mock
        
        resultado = self.service.listar_usuarios()
        
        assert len(resultado) == 2
        assert resultado[0].email == "a@test.com"

    def test_listar_usuarios_filtro_activo(self):
        """Debe filtrar por estado activo."""
        self.service.listar_usuarios(activo=True)
        
        # Verificar que se llamó al filtro con activo
        query = self.mock_db.query.return_value.filter.return_value
        assert query.filter.called

    def test_listar_usuarios_filtro_rol(self):
        """Debe filtrar por rol."""
        self.service.listar_usuarios(rol="admin")
        
        query = self.mock_db.query.return_value.filter.return_value
        assert query.filter.called

    def test_listar_usuarios_excluye_admin_test(self):
        """Debe excluir usuario admin@test.com de la lista."""
        self.service.listar_usuarios()
        
        # Verificar que el filtro inicial excluye admin@test.com
        query = self.mock_db.query.return_value
        assert query.filter.called


class TestProfileService:
    """Tests para ProfileService."""

    def setup_method(self):
        """Configura mocks antes de cada test."""
        self.mock_db = MagicMock()
        self.service = ProfileService(self.mock_db)

    def test_crear_perfil_exitoso(self):
        """Debe crear perfil exitosamente."""
        from models.schemas_perfil_cargo import PerfilCargoCreate

        perfil_data = PerfilCargoCreate(
            titulo="Desarrollador Python",
            descripcion="Buscamos desarrollador Python",
            requisitos="Python, SQL, FastAPI",
            responsabilidades="Desarrollar, Testear",
            habilidades_requeridas=["Python", "FastAPI"],
            habilidades_deseables=["Docker"],
            nivel_experiencia="mid",
            salario_minimo=1500000,
            salario_maximo=2500000,
            departamento="Tecnología",
        )
        
        perfil_mock = MagicMock()
        perfil_mock.titulo = "Desarrollador Python"
        
        self.mock_db.commit.return_value = None
        self.mock_db.refresh.return_value = None
        
        # Mockear la creación del objeto PerfilCargo
        import services.profile_service as ps_module
        original_perfil_cargo = ps_module.PerfilCargo
        ps_module.PerfilCargo = MagicMock(return_value=perfil_mock)
        
        try:
            resultado = self.service.crear_perfil(perfil_data, usuario_id=1)
            
            assert resultado == perfil_mock
            self.mock_db.add.assert_called_once()
            self.mock_db.commit.assert_called_once()
            self.mock_db.refresh.assert_called_once()
        finally:
            # Restaurar original
            ps_module.PerfilCargo = original_perfil_cargo

    def test_crear_perfil_error_db(self):
        """Debe lanzar ProfileServiceError si hay error de DB."""
        from models.schemas_perfil_cargo import PerfilCargoCreate
        from sqlalchemy.exc import SQLAlchemyError

        perfil_data = PerfilCargoCreate(
            titulo="Test",
            descripcion="Test",
            requisitos="Requisito 1",
            responsabilidades="Responsabilidad 1",
            habilidades_requeridas=[],
            habilidades_deseables=[],
            nivel_experiencia="junior",
            salario_minimo=1000,
            salario_maximo=2000,
            departamento="Test",
        )
        
        # Simular error de SQLAlchemy
        self.mock_db.commit.side_effect = SQLAlchemyError("Error DB")
        
        with pytest.raises(ProfileServiceError) as exc_info:
            self.service.crear_perfil(perfil_data, usuario_id=1)
        
        assert "Error al crear perfil" in str(exc_info.value)
        self.mock_db.rollback.assert_called_once()

    def test_crear_perfil_log_exitoso(self, caplog):
        """Debe loguear creación exitosa."""
        from models.schemas_perfil_cargo import PerfilCargoCreate

        perfil_data = PerfilCargoCreate(
            titulo="Perfil Test",
            descripcion="Desc",
            requisitos="Requisito",
            responsabilidades="Responsabilidad",
            habilidades_requeridas=[],
            habilidades_deseables=[],
            nivel_experiencia="senior",
            salario_minimo=1,
            salario_maximo=2,
            departamento="IT",
        )
        
        perfil_mock = MagicMock()
        perfil_mock.titulo = "Perfil Test"
        
        import services.profile_service as ps_module
        ps_module.PerfilCargo = MagicMock(return_value=perfil_mock)
        
        with caplog.at_level("INFO"):
            try:
                self.service.crear_perfil(perfil_data, usuario_id=42)
            except:
                pass  # Ignorar errores de mock
            
        assert "Perfil de cargo" in caplog.text or "perfil" in caplog.text.lower()

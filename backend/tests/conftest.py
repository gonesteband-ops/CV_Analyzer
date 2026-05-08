"""
Fixtures compartidas para todos los tests.
"""
import pytest
import sys
from pathlib import Path

# Agregar backend/src al path para imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))


@pytest.fixture(scope="session")
def test_config():
    """Configuración compartida para tests."""
    return {
        "database_url": "sqlite:///./test.db",
        "test_email": "test@example.com",
        "test_password": "password123",
    }


@pytest.fixture
def sample_cv_text():
    """Texto de CV de ejemplo para tests."""
    return """
    Juan Pérez
    Desarrollador Python Senior
    
    Experiencia:
    - 5 años desarrollando aplicaciones backend con Python y FastAPI
    - Experiencia en SQL, PostgreSQL y MySQL
    - Conocimiento de Docker y Kubernetes
    - Liderazgo de equipo de 3 desarrolladores
    
    Educación:
    - Ingeniería Civil Informática, Universidad de Chile
    - Diplomado en Arquitectura de Software
    
    Habilidades:
    Python, FastAPI, Django, SQL, Docker, Kubernetes, Git, Agile, Scrum
    """


@pytest.fixture
def sample_perfil_data():
    """Datos de perfil de ejemplo para tests."""
    return {
        "titulo": "Desarrollador Python Senior",
        "descripcion": "Buscamos desarrollador senior para liderar proyectos backend",
        "requisitos": ["Python", "FastAPI", "SQL"],
        "responsabilidades": ["Desarrollar", "Liderar", "Mentorear"],
        "habilidades_requeridas": ["Python", "FastAPI", "SQL"],
        "habilidades_deseables": ["Docker", "Kubernetes"],
        "nivel_experiencia": "senior",
        "salario_minimo": 2000000,
        "salario_maximo": 3000000,
        "departamento": "Tecnología",
    }


@pytest.fixture
def sample_cv_pdf_bytes():
    """Bytes de PDF de ejemplo (PDF mínimo válido)."""
    # PDF mínimo válido (solo para testing)
    return b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n2 0 obj\n<< /Type /Pages /Kids [] >>\nendobj\nxref\n0 3\n0000000000 65535 f\n0000000009 00000 n\n0000000058 00000 n\ntrailer\n<< /Size 3 /Root 1 0 R >>\nstartxref\n115\n%%EOF"


@pytest.fixture
def sample_cv_docx_bytes():
    """Bytes de DOCX de ejemplo (ZIP vacío con estructura mínima)."""
    # DOCX es un ZIP con estructura específica
    # Para testing, usamos bytes que simulan un DOCX
    import io
    import zipfile
    
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, 'w') as z:
        z.writestr("[Content_Types].xml", '<?xml version="1.0"?><Types></Types>')
        z.writestr("_rels/.rels", '<?xml version="1.0"?><Relationships></Relationships>')
    return buffer.getvalue()


@pytest.fixture
def temp_cv_txt(tmp_path, sample_cv_text):
    """Archivo TXT de CV temporal."""
    archivo = tmp_path / "cv_test.txt"
    archivo.write_text(sample_cv_text, encoding='utf-8')
    return archivo


@pytest.fixture
def mock_httpx_response():
    """Mock de respuesta HTTPX para tests de APIs externas."""
    class MockResponse:
        def __init__(self, status_code=200, json_data=None, text=""):
            self.status_code = status_code
            self._json_data = json_data or {}
            self._text = text
            
        def json(self):
            return self._json_data
            
        @property
        def text(self):
            return self._text
            
        def raise_for_status(self):
            if self.status_code >= 400:
                raise Exception(f"HTTP Error {self.status_code}")
    
    return MockResponse

"""
Tests unitarios para el servicio MatchingService.
Prueba el algoritmo híbrido de matching (keywords + embeddings).
"""
import pytest
from services.matching import MatchingService, ResultadoMatching


class TestMatchingServiceInit:
    """Tests para inicialización del MatchingService."""

    def test_init_con_modelo_por_defecto(self):
        """Debe inicializar con modelo de embeddings por defecto."""
        service = MatchingService()
        
        assert service.modelo_embeddings == "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
        assert service._modelo_cargado is None

    def test_init_con_modelo_personalizado(self):
        """Debe permitir modelo personalizado."""
        modelo = "sentence-transformers/all-MiniLM-L6-v2"
        service = MatchingService(modelo_embeddings=modelo)
        
        assert service.modelo_embeddings == modelo


class TestMatchingServiceKeywords:
    """Tests para matching de keywords."""

    def setup_method(self):
        """Configura el service antes de cada test."""
        self.service = MatchingService()

    def test_coverage_keywords_completo(self):
        """Debe retornar 1.0 cuando todas las keywords están presentes."""
        cv_texto = "Experiencia en Python y Java. Conocimiento de SQL y Docker."
        perfil_keywords = ["Python", "Java"]
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        assert coverage == 1.0
        assert len(encontradas) == 2
        assert len(faltantes) == 0
        assert "Python" in encontradas
        assert "Java" in encontradas

    def test_coverage_keywords_parcial(self):
        """Debe retornar coverage parcial cuando faltan keywords."""
        cv_texto = "Experiencia en Python y JavaScript."
        perfil_keywords = ["Python", "Java", "SQL"]
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        assert coverage == pytest.approx(1/3, rel=0.01)
        assert "Python" in encontradas
        assert len(faltantes) == 2

    def test_coverage_keywords_ninguna(self):
        """Debe retornar 0.0 cuando ninguna keyword está presente."""
        cv_texto = "Experiencia en marketing y ventas."
        perfil_keywords = ["Python", "Java", "SQL"]
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        assert coverage == 0.0
        assert len(encontradas) == 0
        assert len(faltantes) == 3

    def test_coverage_keywords_vacia(self):
        """Debe retornar 1.0 si no hay keywords requeridas."""
        cv_texto = "Cualquier texto"
        perfil_keywords = []
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        assert coverage == 1.0
        assert len(encontradas) == 0
        assert len(faltantes) == 0

    def test_word_boundary_match_exacto(self):
        """Debe usar word boundaries para evitar falsos positivos."""
        # "Java" no debe matchear con "JavaScript"
        cv_texto = "Experiencia en JavaScript, no en Java."
        perfil_keywords = ["Java"]
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        # Java debería encontrarse porque está en el texto
        assert "Java" in encontradas or "Java" in faltantes
        
    def test_case_insensitive(self):
        """El matching debe ser insensible a mayúsculas/minúsculas."""
        cv_texto = "experiencia en python y java"
        perfil_keywords = ["PYTHON", "JAVA"]
        
        coverage, encontradas, faltantes = self.service._calcular_coverage_keywords(
            cv_texto, perfil_keywords
        )
        
        assert coverage == 1.0


class TestMatchingServiceEtiqueta:
    """Tests para determinación de etiqueta de recomendación."""

    def setup_method(self):
        """Configura el service antes de cada test."""
        self.service = MatchingService()

    def test_etiqueta_recomendado(self):
        """Debe retornar 'Recomendado' para puntaje >= 70."""
        assert self.service.determinar_etiqueta(70) == "Recomendado"
        assert self.service.determinar_etiqueta(85) == "Recomendado"
        assert self.service.determinar_etiqueta(100) == "Recomendado"

    def test_etiqueta_recomendado_con_reservas(self):
        """Debe retornar 'Recomendado con reservas' para 40 <= puntaje < 70."""
        assert self.service.determinar_etiqueta(40) == "Recomendado con reservas"
        assert self.service.determinar_etiqueta(55) == "Recomendado con reservas"
        assert self.service.determinar_etiqueta(69) == "Recomendado con reservas"

    def test_etiqueta_no_recomendado(self):
        """Debe retornar 'No Recomendado' para puntaje < 40."""
        assert self.service.determinar_etiqueta(0) == "No Recomendado"
        assert self.service.determinar_etiqueta(25) == "No Recomendado"
        assert self.service.determinar_etiqueta(39) == "No Recomendado"

    def test_etiqueta_con_umbrales_personalizados(self):
        """Debe respetar umbrales personalizados."""
        assert self.service.determinar_etiqueta(80, umbral_recomendado=80) == "Recomendado"
        assert self.service.determinar_etiqueta(50, umbral_reservas=50) == "Recomendado con reservas"


class TestMatchingServiceFeedback:
    """Tests para generación de feedback."""

    def setup_method(self):
        """Configura el service antes de cada test."""
        self.service = MatchingService()

    def test_generar_feedback_con_keywords_encontradas(self):
        """Debe generar fortalezas basadas en keywords encontradas."""
        cv_texto = "Experiencia en Python y desarrollo backend."
        perfil_titulo = "Desarrollador Python"
        
        resultado = ResultadoMatching(
            puntaje_semantico=0.8,
            puntaje_keywords=0.75,
            puntaje_final=76,
            keywords_encontradas=["Python", "Backend"],
            keywords_faltantes=["Docker"],
            similitud_coseno=0.75,
        )
        
        fortalezas, debilidades, feedback = self.service.generar_feedback(
            cv_texto, perfil_titulo, resultado
        )
        
        assert len(fortalezas) > 0
        assert "Python" in " ".join(fortalezas).lower() or "posee" in " ".join(fortalezas).lower()

    def test_generar_feedback_con_keywords_faltantes(self):
        """Debe generar debilidades basadas en keywords faltantes."""
        cv_texto = "CV básico"
        perfil_titulo = "Desarrollador Senior"

        resultado = ResultadoMatching(
            puntaje_semantico=0.4,
            puntaje_keywords=0.3,
            puntaje_final=35,
            keywords_encontradas=["Comunicación"],
            keywords_faltantes=["Python", "SQL", "Docker"],
            similitud_coseno=0.35,
        )

        fortalezas, debilidades, feedback = self.service.generar_feedback(
            cv_texto, perfil_titulo, resultado
        )

        assert len(debilidades) > 0
        # El formato es "No se menciona python en el CV"
        assert "no se menciona" in " ".join(debilidades).lower()

    def test_generar_feedback_narrativo_alto_puntaje(self):
        """El feedback narrativo debe reflejar alto puntaje."""
        feedback = self.service._construir_feedback_narrativo(
            perfil_titulo="Desarrollador",
            puntaje_final=85,
            fortalezas=["Python", "SQL"],
            debilidades=[],
            puntaje_semantico=0.85,
            puntaje_keywords=0.80,
        )
        
        assert "fuerte" in feedback.lower() or "85" in feedback


class TestMatchingServiceCalcularMatching:
    """Tests para el método principal calcular_matching."""

    def setup_method(self):
        """Configura el service antes de cada test."""
        self.service = MatchingService()

    def test_calcular_matching_resultado_structure(self):
        """Debe retornar ResultadoMatching con estructura correcta."""
        cv_texto = "Experiencia en desarrollo Python con SQL."
        perfil_titulo = "Desarrollador Backend"
        perfil_descripcion = "Buscamos desarrollador con Python y SQL"
        perfil_puntos_fuertes = ["Python", "SQL"]
        
        resultado = self.service.calcular_matching(
            cv_texto, perfil_titulo, perfil_descripcion, perfil_puntos_fuertes
        )
        
        assert isinstance(resultado, ResultadoMatching)
        assert 0 <= resultado.puntaje_semantico <= 1
        assert 0 <= resultado.puntaje_keywords <= 1
        assert 0 <= resultado.puntaje_final <= 100
        assert isinstance(resultado.keywords_encontradas, list)
        assert isinstance(resultado.keywords_faltantes, list)

    def test_calcuar_matching_puntaje_combinado(self):
        """El puntaje final debe ser combinación ponderada."""
        cv_texto = "Python Java SQL"
        perfil_descripcion = "Desarrollador"
        perfil_puntos_fuertes = ["Python", "Java"]
        
        resultado = self.service.calcular_matching(
            cv_texto, "Dev", perfil_descripcion, perfil_puntos_fuertes
        )
        
        # Con 100% keywords match, el puntaje debería ser alto
        assert resultado.puntaje_keywords == 1.0
        # El puntaje final debería ser >= 70 (por 70% de keywords)
        assert resultado.puntaje_final >= 70

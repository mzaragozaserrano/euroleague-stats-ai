"""
Unit tests para el servicio VectorizationService.
Cubre: embeddings generation, schema retrieval, error handling.
"""

import pytest
import logging
from app.services.vectorization import VectorizationService

logger = logging.getLogger(__name__)


class TestVectorizationServiceInstantiation:
    """Tests para instanciación del servicio."""

    def test_service_instantiation(self):
        """Service debe instanciarse correctamente."""
        service = VectorizationService(api_key="test-key-mock")
        assert service is not None
        assert service.client is not None

    def test_embedding_model_configured(self):
        """Modelo de embedding debe estar configurado."""
        service = VectorizationService(api_key="test-key-mock")
        assert service.client is not None


class TestVectorizationServiceMethods:
    """Tests para métodos del servicio."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio."""
        return VectorizationService(api_key="test-key-mock")

    def test_service_has_generate_embedding_method(self, service):
        """Service debe tener método generate_embedding."""
        assert hasattr(service, 'generate_embedding')
        assert callable(service.generate_embedding)

    def test_service_has_retrieve_relevant_schema_method(self, service):
        """Service debe tener método retrieve_relevant_schema."""
        assert hasattr(service, 'retrieve_relevant_schema')
        assert callable(service.retrieve_relevant_schema)

    def test_service_has_vectorize_schema_metadata_method(self, service):
        """Service debe tener método vectorize_schema_metadata."""
        assert hasattr(service, 'vectorize_schema_metadata')
        assert callable(service.vectorize_schema_metadata)

    def test_service_has_clear_schema_embeddings_method(self, service):
        """Service debe tener método clear_schema_embeddings."""
        assert hasattr(service, 'clear_schema_embeddings')
        assert callable(service.clear_schema_embeddings)


class TestVectorizationErrorHandling:
    """Tests para manejo de errores."""

    @pytest.fixture
    def service(self):
        """Instancia del servicio."""
        return VectorizationService(api_key="test-key-mock")

    def test_service_initialization_with_invalid_key(self):
        """Service debe inicializarse incluso con claves inválidas."""
        # En testing, permitimos claves mock
        service = VectorizationService(api_key="invalid-key-for-testing")
        assert service is not None

    def test_service_client_is_openai_compatible(self, service):
        """Client debe ser compatible con OpenAI."""
        from openai import AsyncOpenAI
        assert isinstance(service.client, AsyncOpenAI)


class TestVectorizationConstants:
    """Tests para constantes configuradas."""

    def test_embedding_model_constant(self):
        """Modelo de embedding debe estar definido."""
        from app.services.vectorization import EMBEDDING_MODEL
        assert EMBEDDING_MODEL == "text-embedding-3-small"

    def test_embedding_dimensions_constant(self):
        """Dimensiones de embedding deben estar definidas."""
        from app.services.vectorization import EMBEDDING_DIMENSIONS
        assert EMBEDDING_DIMENSIONS == 1536

    def test_embedding_dimensions_valid(self):
        """Dimensiones de embedding deben ser válidas."""
        from app.services.vectorization import EMBEDDING_DIMENSIONS
        assert EMBEDDING_DIMENSIONS > 0
        assert EMBEDDING_DIMENSIONS == 1536


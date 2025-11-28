# pytest fixtures para testing
import pytest
from httpx import AsyncClient
from app.main import app
from app.config import get_settings


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def settings_fixture():
    """Proporciona la configuración de la aplicación para tests."""
    return get_settings()



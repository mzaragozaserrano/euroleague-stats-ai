# pytest fixtures para testing
import pytest
import logging
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.config import get_settings
from app.database import Base, get_db


# Configurar logging para tests
logging.basicConfig(level=logging.INFO)


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def settings_fixture():
    """Proporciona la configuración de la aplicación para tests."""
    return get_settings()


@pytest.fixture
async def db_session():
    """
    Crea una sesión de BD en memoria para testing.
    
    Nota: En testing real, usaremos test database en Neon.
    Esta es una sesión mock para desarrollo local.
    """
    # Usar SQLite en memoria para testing local
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=NullPool,
        echo=False,
    )
    
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Crear tablas
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Usar sesión para test
    async with async_session_maker() as session:
        yield session
    
    # Cleanup
    await engine.dispose()



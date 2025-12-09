from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool
from app.config import settings

# CRÍTICO: NullPool para Neon Serverless
# connect_args={"statement_cache_size": 0} deshabilita el caché de statements de asyncpg
# Esto es crucial para evitar errores cuando el esquema cambia (InvalidCachedStatementError)
engine = create_async_engine(
    settings.database_url, 
    poolclass=NullPool, 
    echo=settings.environment == "development",
    connect_args={"statement_cache_size": 0}
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with async_session_maker() as session:
        yield session

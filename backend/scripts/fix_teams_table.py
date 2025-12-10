import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def fix():
    async with async_session_maker() as s:
        # Eliminar tabla si existe con esquema incorrecto
        await s.execute(text('DROP TABLE IF EXISTS teams CASCADE'))
        await s.commit()
        
        # Recrear tabla con esquema correcto
        await s.execute(text("""
            CREATE TABLE teams (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                code VARCHAR(10) UNIQUE NOT NULL,
                name VARCHAR(255) NOT NULL,
                logo_url TEXT,
                created_at VARCHAR(50) NOT NULL DEFAULT NOW()::text,
                updated_at VARCHAR(50) NOT NULL DEFAULT NOW()::text
            )
        """))
        await s.execute(text('CREATE INDEX IF NOT EXISTS idx_teams_code ON teams(code)'))
        await s.commit()
        print('Tabla teams corregida')

asyncio.run(fix())




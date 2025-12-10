
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def fix_schema():
    print("Corrigiendo esquema de tablas Games...")
    async with async_session_maker() as s:
        print("Eliminando tablas antiguas...")
        await s.execute(text('DROP TABLE IF EXISTS player_stats_games CASCADE'))
        await s.execute(text('DROP TABLE IF EXISTS games CASCADE'))
        await s.commit()
        print("Tablas eliminadas. Ejecuta init_db.py para recrearlas.")

if __name__ == "__main__":
    asyncio.run(fix_schema())




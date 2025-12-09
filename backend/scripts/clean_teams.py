import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def clean():
    async with async_session_maker() as s:
        await s.execute(text('DELETE FROM teams'))
        await s.commit()
        print('Teams limpiados')

asyncio.run(clean())


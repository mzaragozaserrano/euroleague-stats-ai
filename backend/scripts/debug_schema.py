
import asyncio
from sqlalchemy import text
from app.database import async_session_maker

async def check_columns():
    async with async_session_maker() as session:
        result = await session.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name = 'games'"
        ))
        print("Columns in 'games' table:")
        for row in result.fetchall():
            print(row[0])

if __name__ == "__main__":
    asyncio.run(check_columns())




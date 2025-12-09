import asyncio
from app.database import async_session_maker
from sqlalchemy import text

async def check_positions():
    async with async_session_maker() as session:
        result = await session.execute(text("""
            SELECT p.name, p.position 
            FROM players p 
            JOIN teams t ON p.team_id = t.id 
            WHERE t.name ILIKE '%Real Madrid%' 
            AND p.season = 'E2025' 
            LIMIT 15
        """))
        rows = result.fetchall()
        
        print("\n=== Jugadores Real Madrid (E2025) ===")
        with_position = 0
        without_position = 0
        
        for row in rows:
            name, position = row
            if position:
                print(f"[OK] {name}: {position}")
                with_position += 1
            else:
                print(f"[NO] {name}: SIN POSICION")
                without_position += 1
        
        print(f"\nCon posición: {with_position}, Sin posición: {without_position}")

if __name__ == "__main__":
    asyncio.run(check_positions())


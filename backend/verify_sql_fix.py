#!/usr/bin/env python3
"""
Script para probar directamente el SQL contra la BD.
Demuestra que el sistema funciona correctamente cuando se ejecuta fuera del MCP.
"""
import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import async_session_maker
from sqlalchemy import text

async def main():
    async with async_session_maker() as session:
        print("=" * 80)
        print("PRUEBA 1: SQL CORRECTO (Con temporada 2024-2025)")
        print("=" * 80)
        
        sql_correcto = """
        SELECT p.name, SUM(ps.points) as total_points 
        FROM players p 
        JOIN player_stats_games ps ON p.id = ps.player_id 
        JOIN games g ON ps.game_id = g.id 
        WHERE g.season IN (2024, 2025) 
        GROUP BY p.id, p.name 
        ORDER BY total_points DESC 
        LIMIT 1;
        """
        
        try:
            result = await session.execute(text(sql_correcto))
            rows = result.fetchall()
            cols = result.keys()
            
            if rows:
                print(f"\nResultado:\n{dict(zip(cols, rows[0]))}\n")
            else:
                print("No hay resultados")
        except Exception as e:
            print(f"ERROR: {e}")
        
        print("\n" + "=" * 80)
        print("PRUEBA 2: SQL INCORRECTO (Con temporada 2022 - la que genera MCP cacheado)")
        print("=" * 80)
        
        sql_incorrecto = """
        SELECT p.name, SUM(ps.points) as total_points 
        FROM players p 
        JOIN player_stats_games ps ON p.id = ps.player_id 
        JOIN games g ON ps.game_id = g.id 
        WHERE g.season = '2022' 
        GROUP BY p.id, p.name 
        ORDER BY total_points DESC 
        LIMIT 1;
        """
        
        try:
            result = await session.execute(text(sql_incorrecto))
            rows = result.fetchall()
            cols = result.keys()
            
            if rows:
                print(f"Resultado: {dict(zip(cols, rows[0]))}")
            else:
                print("❌ SIN RESULTADOS (Esperado - season 2022 no existe)\n")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())


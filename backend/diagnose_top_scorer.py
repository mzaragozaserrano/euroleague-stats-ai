#!/usr/bin/env python3
"""
Script para diagnosticar quién es el máximo anotador real en la BD
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.database import async_session_maker
from sqlalchemy import text

async def main():
    async with async_session_maker() as session:
        try:
            # Primero ver qué temporadas y datos hay
            print("=" * 80)
            print("RESUMEN DE DATOS POR TEMPORADA")
            print("=" * 80)
            result = await session.execute(text("""
                SELECT g.season, COUNT(DISTINCT g.id) as num_games, 
                       COUNT(DISTINCT ps.player_id) as num_players,
                       SUM(ps.points) as total_puntos
                FROM games g
                LEFT JOIN player_stats_games ps ON g.id = ps.game_id
                GROUP BY g.season
                ORDER BY g.season DESC
            """))
            for row in result:
                print(f"Temporada {row[0]}: {row[1]} partidos, {row[2]} jugadores, {row[3]} puntos totales")
            
            # Ahora ver el máximo anotador DE TODOS LOS TIEMPOS
            print("\n" + "=" * 80)
            print("TOP 10 MÁXIMOS ANOTADORES (TODAS LAS TEMPORADAS)")
            print("=" * 80)
            result = await session.execute(text("""
                SELECT p.name, SUM(ps.points) as total_points, COUNT(*) as num_games
                FROM players p 
                JOIN player_stats_games ps ON p.id = ps.player_id 
                JOIN games g ON ps.game_id = g.id 
                GROUP BY p.id, p.name 
                ORDER BY total_points DESC 
                LIMIT 10
            """))
            rows = list(result)
            for i, row in enumerate(rows, 1):
                print(f"{i}. {row[0]}: {row[1]} puntos ({row[2]} juegos)")
            
            # Ahora ver el máximo anotador DE 2024-2025
            print("\n" + "=" * 80)
            print("TOP 10 MÁXIMOS ANOTADORES (TEMPORADA 2024-2025)")
            print("=" * 80)
            result = await session.execute(text("""
                SELECT p.name, SUM(ps.points) as total_points, COUNT(*) as num_games
                FROM players p 
                JOIN player_stats_games ps ON p.id = ps.player_id 
                JOIN games g ON ps.game_id = g.id 
                WHERE g.season IN (2024, 2025)
                GROUP BY p.id, p.name 
                ORDER BY total_points DESC 
                LIMIT 10
            """))
            rows = list(result)
            if rows:
                for i, row in enumerate(rows, 1):
                    print(f"{i}. {row[0]}: {row[1]} puntos ({row[2]} juegos)")
            else:
                print("NO HAY DATOS PARA 2024-2025")
            
            # Cuántos jugadores únicos hay
            print("\n" + "=" * 80)
            print("ESTADÍSTICAS GENERALES")
            print("=" * 80)
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT id) as total_jugadores FROM players
            """))
            row = result.fetchone()
            print(f"Total de jugadores en BD: {row[0]}")
            
            result = await session.execute(text("""
                SELECT COUNT(DISTINCT player_id) as jugadores_con_stats FROM player_stats_games
            """))
            row = result.fetchone()
            print(f"Jugadores con estadísticas: {row[0]}")
            
        except Exception as e:
            print(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())


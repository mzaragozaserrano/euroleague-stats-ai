"""
Script de diagnóstico para consultas SQL que no funcionan.
Verifica si un jugador existe y tiene estadísticas.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database import async_session_maker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def diagnose_player_query(player_name: str, season: str = "E2025"):
    """
    Diagnostica por qué una consulta de jugador no funciona.
    
    Args:
        player_name: Nombre del jugador a buscar
        season: Temporada a verificar (default: E2025)
    """
    async with async_session_maker() as session:
        print(f"\n{'='*60}")
        print(f"DIAGNÓSTICO: {player_name} - Temporada {season}")
        print(f"{'='*60}\n")
        
        # 1. Buscar jugador en tabla players
        print("1. Buscando jugador en tabla 'players'...")
        search_query = text("""
            SELECT id, name, team_id, season, player_code
            FROM players
            WHERE name ILIKE :pattern
            ORDER BY name
        """)
        
        result = await session.execute(search_query, {"pattern": f"%{player_name}%"})
        players = result.fetchall()
        
        if not players:
            print(f"   [X] NO se encontro ningun jugador con nombre similar a '{player_name}'")
            print(f"\n   [i] Intentando busqueda mas amplia...")
            
            # Búsqueda más amplia: dividir el nombre en palabras
            words = player_name.split()
            if len(words) > 1:
                first_word = words[0]
                last_word = words[-1]
                print(f"   Buscando jugadores con '{first_word}' o '{last_word}'...")
                
                broad_query = text("""
                    SELECT id, name, team_id, season, player_code
                    FROM players
                    WHERE name ILIKE :first OR name ILIKE :last
                    ORDER BY name
                    LIMIT 10
                """)
                result = await session.execute(broad_query, {
                    "first": f"%{first_word}%",
                    "last": f"%{last_word}%"
                })
                similar_players = result.fetchall()
                
                if similar_players:
                    print(f"   [OK] Encontrados {len(similar_players)} jugadores similares:")
                    for p in similar_players:
                        print(f"      - {p.name} (season: {p.season})")
                else:
                    print(f"   [X] No se encontraron jugadores similares")
        else:
            print(f"   [OK] Encontrados {len(players)} jugador(es):")
            for p in players:
                print(f"      - ID: {p.id}")
                print(f"        Nombre: {p.name}")
                print(f"        Temporada: {p.season}")
                print(f"        Código: {p.player_code}")
                print()
        
        # 2. Verificar si tiene stats en player_season_stats
        print("\n2. Verificando estadísticas en 'player_season_stats'...")
        
        if players:
            for player in players:
                print(f"\n   Jugador: {player.name} (ID: {player.id})")
                
                stats_query = text("""
                    SELECT id, player_id, season, points, rebounds, assists, games_played
                    FROM player_season_stats
                    WHERE player_id = :player_id AND season = :season
                """)
                
                result = await session.execute(stats_query, {
                    "player_id": player.id,
                    "season": season
                })
                stats = result.fetchone()
                
                if stats:
                    print(f"   [OK] Tiene estadisticas para {season}:")
                    print(f"      - Puntos: {stats.points}")
                    print(f"      - Rebotes: {stats.rebounds}")
                    print(f"      - Asistencias: {stats.assists}")
                    print(f"      - Partidos jugados: {stats.games_played}")
                else:
                    print(f"   [X] NO tiene estadisticas para temporada {season}")
                    
                    # Verificar si tiene stats en otras temporadas
                    all_stats_query = text("""
                        SELECT season, points, games_played
                        FROM player_season_stats
                        WHERE player_id = :player_id
                        ORDER BY season DESC
                    """)
                    result = await session.execute(all_stats_query, {"player_id": player.id})
                    all_stats = result.fetchall()
                    
                    if all_stats:
                        print(f"   [i] Pero tiene stats en otras temporadas:")
                        for s in all_stats:
                            print(f"      - {s.season}: {s.points} puntos ({s.games_played} partidos)")
                    else:
                        print(f"   [X] No tiene estadisticas en ninguna temporada")
        else:
            print(f"   [!] No se puede verificar stats porque el jugador no existe")
        
        # 3. Probar la consulta original
        print(f"\n3. Probando consulta original...")
        original_query = text("""
            SELECT p.name AS Jugador, ps.points AS Puntos, ps.season AS Temporada
            FROM players p
            JOIN player_season_stats ps ON p.id = ps.player_id
            WHERE p.name ILIKE :pattern AND ps.season = :season
        """)
        
        try:
            result = await session.execute(original_query, {
                "pattern": f"%{player_name}%",
                "season": season
            })
            rows = result.fetchall()
            
            if rows:
                print(f"   [OK] Consulta retorna {len(rows)} fila(s):")
                for row in rows:
                    print(f"      - {row.Jugador}: {row.Puntos} puntos ({row.Temporada})")
            else:
                print(f"   [X] Consulta retorna 0 filas")
                print(f"\n   [*] Posibles causas:")
                print(f"      1. El jugador no existe en la tabla 'players'")
                print(f"      2. El jugador existe pero no tiene stats en 'player_season_stats' para {season}")
                print(f"      3. El nombre esta almacenado de forma diferente (espacios, acentos, etc.)")
        except Exception as e:
            print(f"   [X] Error ejecutando consulta: {e}")
        
        # 4. Estadísticas generales
        print(f"\n4. Estadísticas generales de la BD...")
        
        count_players = text("SELECT COUNT(*) FROM players WHERE season = :season")
        result = await session.execute(count_players, {"season": season})
        total_players = result.scalar()
        print(f"   - Total jugadores en temporada {season}: {total_players}")
        
        count_stats = text("SELECT COUNT(*) FROM player_season_stats WHERE season = :season")
        result = await session.execute(count_stats, {"season": season})
        total_stats = result.scalar()
        print(f"   - Total registros de stats en temporada {season}: {total_stats}")
        
        if total_players > 0 and total_stats > 0:
            coverage = (total_stats / total_players) * 100
            print(f"   - Cobertura: {coverage:.1f}% de jugadores tienen stats")
        
        print(f"\n{'='*60}\n")


async def main():
    """Función principal."""
    import sys
    
    if len(sys.argv) < 2:
        print("Uso: python diagnose_query.py <nombre_jugador> [temporada]")
        print("Ejemplo: python diagnose_query.py 'Sylvan Francisco' E2025")
        return
    
    player_name = sys.argv[1]
    season = sys.argv[2] if len(sys.argv) > 2 else "E2025"
    
    await diagnose_player_query(player_name, season)


if __name__ == "__main__":
    asyncio.run(main())


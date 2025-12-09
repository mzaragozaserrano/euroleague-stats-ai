"""
Script para verificar equipos en la base de datos.
Útil para diagnosticar problemas de búsqueda de equipos.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Agregar el directorio backend al path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.database import async_session_maker
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def list_all_teams():
    """Lista todos los equipos en la base de datos."""
    try:
        async with async_session_maker() as session:
            stmt = text("SELECT code, name FROM teams ORDER BY name")
            result = await session.execute(stmt)
            teams = result.fetchall()
            
            logger.info(f"Total de equipos en BD: {len(teams)}")
            print("\n=== EQUIPOS EN LA BASE DE DATOS ===\n")
            for team in teams:
                print(f"  {team.code:5s} - {team.name}")
            
            return teams
            
    except Exception as e:
        logger.error(f"Error listando equipos: {e}")
        raise


async def search_team_by_name(search_term: str):
    """Busca equipos por nombre (búsqueda flexible)."""
    try:
        async with async_session_maker() as session:
            # Búsqueda flexible con ILIKE
            stmt = text("""
                SELECT code, name 
                FROM teams 
                WHERE name ILIKE :pattern
                ORDER BY name
            """)
            pattern = f"%{search_term}%"
            result = await session.execute(stmt, {"pattern": pattern})
            teams = result.fetchall()
            
            logger.info(f"Equipos encontrados con '{search_term}': {len(teams)}")
            if teams:
                print(f"\n=== EQUIPOS ENCONTRADOS CON '{search_term}' ===\n")
                for team in teams:
                    print(f"  {team.code:5s} - {team.name}")
            else:
                print(f"\n❌ No se encontraron equipos con '{search_term}'")
            
            return teams
            
    except Exception as e:
        logger.error(f"Error buscando equipo: {e}")
        raise


async def check_team_players(team_code: str = None, team_name_pattern: str = None, season: str = "E2025"):
    """Verifica jugadores de un equipo específico."""
    try:
        async with async_session_maker() as session:
            if team_code:
                stmt = text("""
                    SELECT p.name AS jugador, t.code AS equipo, t.name AS nombre_equipo, p.season
                    FROM players p
                    JOIN teams t ON p.team_id = t.id
                    WHERE t.code = :code AND p.season = :season
                    ORDER BY p.name
                """)
                result = await session.execute(stmt, {"code": team_code, "season": season})
            elif team_name_pattern:
                stmt = text("""
                    SELECT p.name AS jugador, t.code AS equipo, t.name AS nombre_equipo, p.season
                    FROM players p
                    JOIN teams t ON p.team_id = t.id
                    WHERE t.name ILIKE :pattern AND p.season = :season
                    ORDER BY p.name
                """)
                pattern = f"%{team_name_pattern}%"
                result = await session.execute(stmt, {"pattern": pattern, "season": season})
            else:
                logger.error("Debe proporcionar team_code o team_name_pattern")
                return []
            
            players = result.fetchall()
            
            if players:
                print(f"\n=== JUGADORES ENCONTRADOS ===\n")
                print(f"Equipo: {players[0].nombre_equipo} ({players[0].equipo})")
                print(f"Temporada: {players[0].season}")
                print(f"Total: {len(players)} jugadores\n")
                for player in players:
                    print(f"  - {player.jugador}")
            else:
                print(f"\n❌ No se encontraron jugadores")
            
            return players
            
    except Exception as e:
        logger.error(f"Error verificando jugadores: {e}")
        raise


async def main():
    """Función principal."""
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "list":
            await list_all_teams()
        elif command == "search":
            if len(sys.argv) < 3:
                print("Uso: python check_teams.py search <nombre>")
                return
            search_term = sys.argv[2]
            await search_team_by_name(search_term)
        elif command == "players":
            if len(sys.argv) < 3:
                print("Uso: python check_teams.py players <code|name> <valor> [season]")
                print("Ejemplo: python check_teams.py players code RM")
                print("Ejemplo: python check_teams.py players name 'Hapoel'")
                return
            search_type = sys.argv[2]
            search_value = sys.argv[3]
            season = sys.argv[4] if len(sys.argv) > 4 else "E2025"
            
            if search_type == "code":
                await check_team_players(team_code=search_value, season=season)
            elif search_type == "name":
                await check_team_players(team_name_pattern=search_value, season=season)
            else:
                print("Tipo de búsqueda debe ser 'code' o 'name'")
        else:
            print("Comandos disponibles:")
            print("  list                    - Lista todos los equipos")
            print("  search <nombre>         - Busca equipos por nombre")
            print("  players code <code>     - Muestra jugadores por código de equipo")
            print("  players name <nombre>   - Muestra jugadores por nombre de equipo")
    else:
        # Por defecto, listar todos los equipos
        await list_all_teams()
        print("\n" + "="*50)
        print("\nBuscando 'Hapoel'...")
        await search_team_by_name("Hapoel")
        print("\nBuscando 'Tel Aviv'...")
        await search_team_by_name("Tel Aviv")


if __name__ == "__main__":
    asyncio.run(main())


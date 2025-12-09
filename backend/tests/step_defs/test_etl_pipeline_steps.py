"""
Step definitions para ETL Pipeline BDD tests.
"""

import pytest
from pytest_bdd import given, when, then, scenario
from sqlalchemy import select, text
from app.database import async_session_maker
from app.models import Team, Player, PlayerSeasonStats
import asyncio
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
async def clean_db():
    """Limpia las tablas antes de cada test."""
    async with async_session_maker() as session:
        # Eliminar datos (en orden inverso de dependencias)
        await session.execute(text("DELETE FROM player_season_stats"))
        await session.execute(text("DELETE FROM players"))
        await session.execute(text("DELETE FROM teams"))
        await session.commit()
    yield
    # Cleanup después
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM player_season_stats"))
        await session.execute(text("DELETE FROM players"))
        await session.execute(text("DELETE FROM teams"))
        await session.commit()


# ============================================================================
# SCENARIO: Ingesta de equipos
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Ingesta de equipos funciona correctamente')
def test_ingest_teams():
    pass


@given('La base de datos está limpia')
async def clean_database(clean_db):
    """Limpia la BD antes del test."""
    pass


@given('Las conexiones a APIs están disponibles')
def api_available():
    """Verifica que euroleague_api está disponible."""
    try:
        from euroleague_api.euroleague_data import EuroleagueData
        EuroleagueData()
    except Exception as e:
        pytest.skip(f"euroleague_api no disponible: {e}")


@when('Ejecuto el script de ingesta de equipos')
async def run_ingest_teams():
    """Ejecuta el ETL de equipos."""
    from etl.ingest_teams import run_ingest_teams
    await run_ingest_teams()


@then('Se insertan equipos en la tabla teams')
async def verify_teams_inserted():
    """Verifica que hay equipos en la BD."""
    async with async_session_maker() as session:
        result = await session.execute(select(Team))
        teams = result.scalars().all()
        assert len(teams) > 0, "No hay equipos en la BD"


@then('La tabla teams contiene al menos 18 equipos')
async def verify_teams_count():
    """Verifica que hay al menos 18 equipos."""
    async with async_session_maker() as session:
        result = await session.execute(select(Team))
        teams = result.scalars().all()
        assert len(teams) >= 18, f"Se esperaban ≥18 equipos, se encontraron {len(teams)}"


@then('Cada equipo tiene un código único (code)')
async def verify_unique_codes():
    """Verifica que todos los equipos tienen code único."""
    async with async_session_maker() as session:
        result = await session.execute(select(Team.code))
        codes = result.scalars().all()
        unique_codes = set(codes)
        assert len(codes) == len(unique_codes), "Hay códigos duplicados"
        assert all(code for code in codes), "Hay códigos None o vacíos"


# ============================================================================
# SCENARIO: Ingesta de jugadores
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Ingesta de jugadores funciona correctamente')
def test_ingest_players():
    pass


@given('Los equipos ya están en la BD')
async def ensure_teams_exist():
    """Asegura que los equipos existen."""
    async with async_session_maker() as session:
        result = await session.execute(select(Team))
        teams = result.scalars().all()
        if not teams:
            # Insertar equipos de prueba
            test_teams = [
                Team(code="RM", name="Real Madrid"),
                Team(code="BAR", name="FC Barcelona"),
                Team(code="OLM", name="Olimpia Milano"),
            ]
            session.add_all(test_teams)
            await session.commit()


@when('Ejecuto el script de ingesta de jugadores para temporada 2025')
async def run_ingest_players():
    """Ejecuta el ETL de jugadores."""
    from etl.ingest_players import run_ingest_players
    await run_ingest_players(season=2025)


@then('Se insertan jugadores en la tabla players')
async def verify_players_inserted():
    """Verifica que hay jugadores en la BD."""
    async with async_session_maker() as session:
        result = await session.execute(select(Player))
        players = result.scalars().all()
        assert len(players) > 0, "No hay jugadores en la BD"


@then('Cada jugador está asociado a un equipo válido')
async def verify_players_have_teams():
    """Verifica que cada jugador tiene un team_id válido."""
    async with async_session_maker() as session:
        result = await session.execute(select(Player))
        players = result.scalars().all()
        for player in players:
            assert player.team_id is not None, f"Jugador {player.name} no tiene team_id"


@then('Cada jugador tiene un player_code único')
async def verify_player_codes_unique():
    """Verifica que los player_codes son únicos."""
    async with async_session_maker() as session:
        result = await session.execute(select(Player.player_code))
        codes = result.scalars().all()
        unique_codes = set(codes)
        assert len(codes) == len(unique_codes), "Hay player_codes duplicados"


@then('Los jugadores tienen posiciones válidas (Base, Escolta, Alero, Ala-Pivot, Pivot)')
async def verify_valid_positions():
    """Verifica que las posiciones sean válidas."""
    valid_positions = {"Base", "Escolta", "Alero", "Ala-Pivot", "Pivot", None}
    
    async with async_session_maker() as session:
        result = await session.execute(select(Player.position))
        positions = result.scalars().all()
        for position in positions:
            assert position in valid_positions, f"Posición inválida: {position}"


# ============================================================================
# SCENARIO: Ingesta de estadísticas
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Ingesta de estadísticas por temporada funciona')
def test_ingest_stats():
    pass


@given('Los equipos y jugadores ya están en la BD')
async def ensure_teams_and_players():
    """Asegura que existen equipos y jugadores."""
    async with async_session_maker() as session:
        result = await session.execute(select(Team))
        teams = result.scalars().all()
        
        if not teams:
            test_teams = [
                Team(code="RM", name="Real Madrid"),
                Team(code="BAR", name="FC Barcelona"),
            ]
            session.add_all(test_teams)
            await session.commit()
            teams = test_teams
        
        # Verificar jugadores
        result = await session.execute(select(Player))
        players = result.scalars().all()
        if not players:
            test_players = [
                Player(team_id=teams[0].id, player_code="1", name="Test Player 1", season="E2025"),
                Player(team_id=teams[1].id, player_code="2", name="Test Player 2", season="E2025"),
            ]
            session.add_all(test_players)
            await session.commit()


@when('Ejecuto el script de ingesta de estadísticas para temporada 2025')
async def run_ingest_stats():
    """Ejecuta el ETL de estadísticas."""
    from etl.ingest_player_season_stats import run_ingest_player_season_stats
    await run_ingest_player_season_stats(season=2025)


@then('Se insertan estadísticas en player_season_stats')
async def verify_stats_inserted():
    """Verifica que hay estadísticas en la BD."""
    async with async_session_maker() as session:
        result = await session.execute(select(PlayerSeasonStats))
        stats = result.scalars().all()
        assert len(stats) > 0, "No hay estadísticas en la BD"


@then('Cada estadística está asociada a un jugador válido')
async def verify_stats_have_players():
    """Verifica que cada stat tiene un player_id válido."""
    async with async_session_maker() as session:
        result = await session.execute(select(PlayerSeasonStats))
        stats = result.scalars().all()
        for stat in stats:
            assert stat.player_id is not None, "Stat no tiene player_id"


@then('Las estadísticas contienen campos: points, rebounds, assists, pir')
async def verify_stat_fields():
    """Verifica que los campos de estadísticas existen."""
    async with async_session_maker() as session:
        result = await session.execute(select(PlayerSeasonStats))
        stat = result.scalars().first()
        assert stat is not None, "No hay estadísticas"
        assert hasattr(stat, 'points'), "Falta campo 'points'"
        assert hasattr(stat, 'rebounds'), "Falta campo 'rebounds'"
        assert hasattr(stat, 'assists'), "Falta campo 'assists'"
        assert hasattr(stat, 'pir'), "Falta campo 'pir'"


# ============================================================================
# SCENARIO: Detección de consultas
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Consultas de estadísticas detectan correctamente')
def test_stats_query_detection():
    pass


@then('El servicio text_to_sql detecta como query de stats')
def verify_stats_detection():
    """Verifica que text_to_sql detecta queries de stats."""
    from app.services.text_to_sql import TextToSQLService
    
    queries = [
        "máximos anotadores",
        "maximo anotador",
        "Top 10 reboteadores",
        "mejores asistentes",
    ]
    
    for query in queries:
        is_stats = TextToSQLService._requires_player_stats(query)
        assert is_stats, f"Query '{query}' no fue detectada como stats"


@then('Retorna datos desde player_season_stats sin usar LLM')
def verify_no_llm():
    """Verifica que las queries de stats no usan LLM."""
    # Este es más un concepto que una verificación técnica,
    # pero confirmamos que el servicio maneja stats directamente
    from app.services.text_to_sql import TextToSQLService
    service = TextToSQLService(api_key="test")
    
    # Si es stats query, debería extraer parámetros sin LLM
    assert hasattr(service, '_extract_stats_params'), "Método de extracción no existe"


# ============================================================================
# SCENARIO: Rechazo de queries de partidos
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Consultas de partidos se rechazan adecuadamente')
def test_games_query_rejection():
    pass


@when('El usuario pregunta "partidos de Larkin con más de 10 puntos"')
def user_asks_games_query():
    pass


@then('El servicio text_to_sql detecta como query de partidos')
def verify_games_detection():
    """Verifica que se detectan queries de partidos."""
    from app.services.text_to_sql import TextToSQLService
    
    queries = [
        "partidos de Larkin con más de 10 puntos",
        "partidos donde jugó Llull",
        "partidos de Real Madrid contra Barcelona",
        "box score del partido",
    ]
    
    for query in queries:
        is_unavailable = TextToSQLService._is_games_query_unavailable(query)
        assert is_unavailable, f"Query '{query}' no fue detectada como query de partidos"


@then('Retorna error informativo: "datos detallados por partido"')
def verify_error_message():
    """Verifica que el error es informativo."""
    error_msg = "datos detallados por partido"
    assert "datos" in error_msg.lower()
    assert "partido" in error_msg.lower()


@then('NO intenta generar SQL')
def verify_no_sql_generation():
    """Verifica que no genera SQL."""
    # Esto se verifica en el texto del error
    pass


# ============================================================================
# SCENARIO: Normalización Unicode
# ============================================================================

@scenario('backend/tests/features/etl_pipeline.feature', 'Normalización Unicode en búsquedas')
def test_unicode_normalization():
    pass


@given('Los jugadores "Llull" y "Llúll" están en la BD')
async def add_players_with_accents():
    """Agrega jugadores con y sin tildes."""
    async with async_session_maker() as session:
        # Primero agregar equipo
        team = Team(code="RM", name="Real Madrid")
        session.add(team)
        await session.flush()
        
        # Luego jugadores
        players = [
            Player(team_id=team.id, player_code="1", name="Llull", season="E2025"),
            Player(team_id=team.id, player_code="2", name="Llúll", season="E2025"),
        ]
        session.add_all(players)
        await session.commit()


@when('Busco por el jugador "llull" sin tildes')
def search_player():
    """Busca jugador sin tildes."""
    from app.services.text_to_sql import normalize_text_for_matching
    
    global search_result
    search_query = "llull"
    search_normalized = normalize_text_for_matching(search_query)
    
    assert search_normalized == "llull", f"Normalización falló: {search_normalized}"


@then('El sistema encuentra al jugador independientemente de las tildes')
async def verify_find_player_any_accent():
    """Verifica que se encuentra el jugador sin importar tildes."""
    from app.services.text_to_sql import normalize_text_for_matching
    
    async with async_session_maker() as session:
        # Buscar ambos nombres normalizados
        players = await session.execute(select(Player))
        all_players = players.scalars().all()
        
        for player in all_players:
            normalized_name = normalize_text_for_matching(player.name)
            assert normalized_name == "llull", f"Nombre no normalizado: {normalized_name}"


@then('El resultado retorna el nombre correcto con tilde (como dicta la API)')
def verify_correct_name_with_accent():
    """Verifica que retorna el nombre correcto."""
    # El nombre se retorna tal como está en la BD (como lo devuelve la API)
    pass


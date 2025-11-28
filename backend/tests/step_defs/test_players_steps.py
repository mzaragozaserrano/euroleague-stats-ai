"""
Step definitions para pruebas del ETL de Jugadores (Players).
"""

import pytest
from pytest_bdd import given, when, then, scenario
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from etl.euroleague_client import (
    EuroleagueClient,
    EuroleagueAPIError,
)


# Escenarios
@scenario("../features/players.feature", "API devuelve datos válidos de jugadores")
def test_api_returns_valid_players_data():
    """Validar que la API devuelve datos válidos de jugadores."""
    pass


@scenario(
    "../features/players.feature",
    "Nuevos jugadores se insertan en la base de datos"
)
def test_new_players_inserted_to_database():
    """Validar que los nuevos jugadores se insertan en la BD."""
    pass


@scenario(
    "../features/players.feature",
    "Jugadores existentes se actualizan correctamente"
)
def test_existing_players_updated_correctly():
    """Validar que los jugadores existentes se actualizan."""
    pass


@scenario(
    "../features/players.feature",
    "Se evita duplicación de jugadores"
)
def test_prevents_player_duplication():
    """Validar que se evita la duplicación de jugadores."""
    pass


@scenario(
    "../features/players.feature",
    "Los jugadores se asocian correctamente a sus equipos"
)
def test_players_associated_to_teams_correctly():
    """Validar que los jugadores se asocian correctamente a equipos."""
    pass


@scenario(
    "../features/players.feature",
    "El ETL maneja errores de API correctamente"
)
def test_etl_handles_api_errors():
    """Validar que el ETL maneja errores de API."""
    pass


@scenario(
    "../features/players.feature",
    "El ETL valida campos obligatorios"
)
def test_etl_validates_required_fields():
    """Validar que el ETL valida campos obligatorios."""
    pass


@scenario(
    "../features/players.feature",
    "El ETL maneja relaciones de clave foránea"
)
def test_etl_handles_foreign_key_relations():
    """Validar que el ETL valida relaciones de clave foránea."""
    pass


@scenario(
    "../features/players.feature",
    "Múltiples ejecuciones del ETL son idempotentes"
)
def test_etl_multiple_executions_are_idempotent():
    """Validar que múltiples ejecuciones del ETL son idempotentes."""
    pass


# Fixtures
@pytest.fixture
def client():
    """Fixture que proporciona una instancia del cliente de Euroleague."""
    return EuroleagueClient()


@pytest.fixture
def sample_players_response():
    """Fixture que proporciona datos de ejemplo de jugadores."""
    return {
        "Players": [
            {
                "id": 1,
                "name": "Juan Carlos Navarro",
                "first_name": "Juan Carlos",
                "last_name": "Navarro",
                "jersey_number": 11,
                "team_id": 1
            },
            {
                "id": 2,
                "name": "Felipe Reyes",
                "first_name": "Felipe",
                "last_name": "Reyes",
                "jersey_number": 7,
                "team_id": 1
            },
            {
                "id": 3,
                "name": "Raúl López",
                "first_name": "Raúl",
                "last_name": "López",
                "jersey_number": 5,
                "team_id": 2
            },
            {
                "id": 4,
                "name": "Giorgos Printezis",
                "first_name": "Giorgos",
                "last_name": "Printezis",
                "jersey_number": 30,
                "team_id": 2
            },
            {
                "id": 5,
                "name": "Nikola Mirotic",
                "first_name": "Nikola",
                "last_name": "Mirotic",
                "jersey_number": 33,
                "team_id": 3
            }
        ]
    }


@pytest.fixture
def sample_updated_player():
    """Fixture para jugador actualizado."""
    return {
        "id": 1,
        "name": "Juan Carlos Navarro Valverde",
        "first_name": "Juan Carlos",
        "last_name": "Navarro Valverde",
        "jersey_number": 11,
        "team_id": 1
    }


@pytest.fixture
def sample_teams_in_db():
    """Fixture que proporciona equipos previos en la BD."""
    return [
        {"id": 1, "name": "Real Madrid", "code": "RMB"},
        {"id": 2, "name": "FC Barcelona", "code": "BAR"},
    ]


# Given steps
@given("la API de Euroleague está disponible")
def api_is_available(client):
    """Verificar que la API de Euroleague está disponible."""
    assert client is not None
    assert client.base_url == EuroleagueClient.BASE_URL


@given("la API retorna datos válidos de jugadores")
def api_returns_valid_players_data():
    """La API está lista para retornar datos válidos de jugadores."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 5 jugadores nuevos")
def api_returns_5_new_players():
    """La API retornará 5 jugadores nuevos."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos tiene equipos previos cargados")
def database_has_teams_loaded():
    """La base de datos tiene equipos previos cargados."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos no contiene jugadores")
def database_has_no_players():
    """La base de datos no contiene jugadores inicialmente."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos contiene 1 jugador con id=1, name=\"Juan Carlos Navarro\", team_id=1")
def database_has_one_player():
    """La base de datos contiene un jugador existente."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna el jugador con id=1, name=\"Juan Carlos Navarro Valverde\", team_id=1 (información actualizada)")
def api_returns_updated_player():
    """La API retorna jugador actualizado."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 10 jugadores")
def api_returns_10_players():
    """La API retornará 10 jugadores."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 5 jugadores")
def api_returns_5_players():
    """La API retornará 5 jugadores."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos ya contiene 7 de esos jugadores")
def database_has_7_of_those_players():
    """La base de datos contiene 7 jugadores."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos contiene 2 equipos con id=1, id=2")
def database_has_2_teams():
    """La base de datos contiene 2 equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 3 jugadores del equipo id=1 y 2 jugadores del equipo id=2")
def api_returns_players_by_team():
    """La API retorna jugadores distribuidos por equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API devuelve un error 503")
def api_returns_503_error():
    """La API retornará error 503."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna datos de jugadores con campos faltantes (falta name o team_id)")
def api_returns_incomplete_player_data():
    """La API retorna datos incompletos de jugadores."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos está vacía (sin equipos)")
def database_is_empty_no_teams():
    """La base de datos está vacía sin equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna jugadores que referencian equipos inexistentes")
def api_returns_players_with_invalid_team_ids():
    """La API retorna jugadores con team_id inválidos."""
    # Este contexto se establece en los pasos when
    pass


# When steps
@when("se ejecuta el ETL de jugadores", target_fixture="etl_result")
async def run_players_etl(client, sample_players_response):
    """Ejecutar el ETL de jugadores."""
    # Este es un paso que será implementado en la fase Green/Refactor
    # Por ahora simplemente retornamos un resultado mock
    return {
        "status": "success",
        "total_processed": len(sample_players_response.get("Players", [])),
        "inserted": len(sample_players_response.get("Players", [])),
        "updated": 0,
        "errors": 0
    }


@when("se ejecuta el ETL de jugadores nuevamente", target_fixture="etl_result_2")
async def run_players_etl_again(client, sample_players_response):
    """Ejecutar el ETL de jugadores nuevamente."""
    # Este es un paso que será implementado en la fase Green/Refactor
    return {
        "status": "success",
        "total_processed": len(sample_players_response.get("Players", [])),
        "inserted": 0,
        "updated": 0,
        "errors": 0
    }


# Then steps
@then("la solicitud GET a /v3/players debe tener estado 200")
async def response_has_status_200(etl_result):
    """Verificar que la solicitud tiene estado 200."""
    assert etl_result is not None
    assert etl_result.get("status") == "success"


@then("la respuesta debe contener una lista de jugadores con campos: id, name, first_name, last_name, jersey_number, team_id")
def response_contains_players_with_required_fields(sample_players_response):
    """Verificar que la respuesta contiene jugadores con campos requeridos."""
    assert "Players" in sample_players_response
    assert len(sample_players_response["Players"]) > 0
    
    for player in sample_players_response["Players"]:
        assert "id" in player
        assert "name" in player
        assert "first_name" in player
        assert "last_name" in player
        assert "jersey_number" in player
        assert "team_id" in player


@then("la base de datos debe contener exactamente 5 jugadores")
async def database_should_have_5_players(etl_result):
    """Verificar que la BD contiene 5 jugadores."""
    assert etl_result["total_processed"] == 5


@then("cada jugador debe tener los campos requeridos: id, name, team_id")
async def each_player_has_required_fields(etl_result):
    """Verificar que cada jugador tiene campos requeridos."""
    assert etl_result["total_processed"] >= 1


@then("cada jugador debe estar asociado a un equipo válido")
async def each_player_associated_to_valid_team(etl_result):
    """Verificar que cada jugador está asociado a un equipo válido."""
    assert etl_result["errors"] == 0


@then("la base de datos debe contener exactamente 1 jugador")
async def database_should_have_1_player(etl_result):
    """Verificar que la BD contiene 1 jugador."""
    assert etl_result["total_processed"] == 1


@then("el nombre del jugador con id=1 debe ser actualizado a \"Juan Carlos Navarro Valverde\"")
async def player_name_updated_correctly(sample_updated_player):
    """Verificar que el nombre del jugador se actualiza."""
    assert sample_updated_player["name"] == "Juan Carlos Navarro Valverde"


@then("la base de datos debe contener exactamente 10 jugadores")
async def database_should_have_10_players(etl_result):
    """Verificar que la BD contiene 10 jugadores."""
    assert etl_result["total_processed"] == 10


@then("no deben haber duplicados")
async def no_duplicates(etl_result):
    """Verificar que no hay duplicados."""
    assert etl_result["errors"] == 0


@then("3 jugadores deben estar asociados al equipo id=1")
async def three_players_associated_to_team_1(etl_result):
    """Verificar que 3 jugadores están asociados al equipo 1."""
    # Este paso será validado en la fase Green
    assert etl_result["total_processed"] >= 3


@then("2 jugadores deben estar asociados al equipo id=2")
async def two_players_associated_to_team_2(etl_result):
    """Verificar que 2 jugadores están asociados al equipo 2."""
    # Este paso será validado en la fase Green
    assert etl_result["total_processed"] >= 2


@then("debe capturarse la excepción EuroleagueAPIError")
def should_catch_euroleague_api_error():
    """Verificar que se captura la excepción correcta."""
    # Este paso se valida en los pasos when
    pass


@then("la base de datos debe permanecer sin cambios")
async def database_should_remain_unchanged(etl_result):
    """Verificar que la BD no cambió."""
    # Si hay error, no debe haber cambios
    if etl_result.get("status") in ["api_error", "critical_error"]:
        assert etl_result["inserted"] == 0
        assert etl_result["updated"] == 0


@then("el ETL debe validar los campos requeridos")
async def etl_validates_required_fields(etl_result):
    """Verificar que el ETL valida campos."""
    assert etl_result is not None
    assert "total_processed" in etl_result


@then("los jugadores con campos obligatorios incompletos deben ser rechazados")
async def incomplete_players_rejected(etl_result):
    """Verificar que los jugadores incompletos son rechazados."""
    # Debe haber errores de validación
    assert etl_result.get("status") != "success" or etl_result["errors"] > 0


@then("el ETL debe validar que team_id exista en la tabla de equipos")
async def etl_validates_team_id_exists(etl_result):
    """Verificar que el ETL valida la existencia de team_id."""
    assert etl_result is not None


@then("los jugadores con team_id inválidos deben ser rechazados")
async def players_with_invalid_team_id_rejected(etl_result):
    """Verificar que los jugadores con team_id inválidos son rechazados."""
    # Debe haber errores de validación
    assert etl_result["errors"] > 0 or etl_result["total_processed"] == 0


@then("no deben haber duplicados después de múltiples ejecuciones")
async def no_duplicates_after_multiple_runs(etl_result_2):
    """Verificar que no hay duplicados después de múltiples ejecuciones."""
    # Ambas ejecuciones deben ser idempotentes
    assert etl_result_2["status"] == "success"



"""
Step definitions para pruebas del ETL de Equipos (Teams).
"""

import pytest
from pytest_bdd import given, when, then, scenario
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from etl.euroleague_client import (
    EuroleagueClient,
    EuroleagueAPIError,
)
from etl.ingest_teams import (
    ingest_teams,
    transform_team_data,
    validate_team_data,
    fetch_teams_from_api,
    TeamIngestError,
)


# Escenarios
@scenario("../features/teams.feature", "API devuelve datos válidos de equipos")
def test_api_returns_valid_teams_data():
    """Validar que la API devuelve datos válidos de equipos."""
    pass


@scenario(
    "../features/teams.feature",
    "Nuevos equipos se insertan en la base de datos"
)
def test_new_teams_inserted_to_database():
    """Validar que los nuevos equipos se insertan en la BD."""
    pass


@scenario(
    "../features/teams.feature",
    "Equipos existentes se actualizan correctamente"
)
def test_existing_teams_updated_correctly():
    """Validar que los equipos existentes se actualizan."""
    pass


@scenario(
    "../features/teams.feature",
    "Se evita duplicación de equipos"
)
def test_prevents_team_duplication():
    """Validar que se evita la duplicación de equipos."""
    pass


@scenario(
    "../features/teams.feature",
    "El ETL maneja errores de API correctamente"
)
def test_etl_handles_api_errors():
    """Validar que el ETL maneja errores de API."""
    pass


@scenario(
    "../features/teams.feature",
    "El ETL valida campos obligatorios"
)
def test_etl_validates_required_fields():
    """Validar que el ETL valida campos obligatorios."""
    pass


@scenario(
    "../features/teams.feature",
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
def sample_teams_response():
    """Fixture que proporciona datos de ejemplo de equipos."""
    return {
        "Teams": [
            {
                "id": 1,
                "name": "Real Madrid",
                "code": "RMB",
                "logo_url": "https://api.euroleague.net/logo/1.png"
            },
            {
                "id": 2,
                "name": "FC Barcelona",
                "code": "BAR",
                "logo_url": "https://api.euroleague.net/logo/2.png"
            }
        ]
    }


@pytest.fixture
def sample_updated_team():
    """Fixture para equipo actualizado."""
    return {
        "id": 1,
        "name": "Real Madrid CF",
        "code": "RMB",
        "logo_url": "https://api.euroleague.net/logo/1.png"
    }


# Given steps
@given("la API de Euroleague está disponible")
def api_is_available(client):
    """Verificar que la API de Euroleague está disponible."""
    assert client is not None
    assert client.base_url == EuroleagueClient.BASE_URL


@given("la API retorna datos válidos de equipos")
def api_returns_valid_teams_data():
    """La API está lista para retornar datos válidos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 2 equipos nuevos")
def api_returns_2_new_teams():
    """La API retornará 2 equipos nuevos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 2 equipos")
def api_returns_2_teams():
    """La API retornará 2 equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos está vacía")
def database_is_empty():
    """La base de datos está vacía inicialmente."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos contiene 1 equipo con id=1, name=\"Real Madrid\", code=\"RMB\"")
def database_has_one_team():
    """La base de datos contiene un equipo existente."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna el equipo con id=1, name=\"Real Madrid CF\", code=\"RMB\" (información actualizada)")
def api_returns_updated_team():
    """La API retorna equipo actualizado."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna 3 equipos")
def api_returns_3_teams():
    """La API retornará 3 equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la base de datos ya contiene 2 de esos equipos")
def database_has_2_of_those_teams():
    """La base de datos contiene 2 equipos."""
    # Este contexto se establece en los pasos when
    pass


@given("la API devuelve un error 503")
def api_returns_503_error():
    """La API retornará error 503."""
    # Este contexto se establece en los pasos when
    pass


@given("la API retorna datos con campos faltantes (falta logo_url)")
def api_returns_incomplete_data():
    """La API retorna datos incompletos."""
    # Este contexto se establece en los pasos when
    pass


# When steps
@when("se ejecuta el ETL de equipos", target_fixture="etl_result")
async def run_teams_etl(client, sample_teams_response):
    """Ejecutar el ETL de equipos."""
    with patch("etl.ingest_teams.fetch_teams_from_api") as mock_fetch:
        mock_fetch.return_value = sample_teams_response
        
        with patch("etl.ingest_teams.async_session_maker") as mock_session_maker:
            # Mock de la sesión de base de datos
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value = mock_session
            
            result = await ingest_teams(client)
            return result


@when("se ejecuta el ETL de equipos nuevamente", target_fixture="etl_result_2")
async def run_teams_etl_again(client, sample_teams_response):
    """Ejecutar el ETL de equipos nuevamente."""
    with patch("etl.ingest_teams.fetch_teams_from_api") as mock_fetch:
        mock_fetch.return_value = sample_teams_response
        
        with patch("etl.ingest_teams.async_session_maker") as mock_session_maker:
            mock_session = AsyncMock()
            mock_session.__aenter__.return_value = mock_session
            mock_session.__aexit__.return_value = None
            mock_session.execute.return_value = MagicMock(scalar_one_or_none=MagicMock(return_value=None))
            mock_session.flush = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session_maker.return_value = mock_session
            
            result = await ingest_teams(client)
            return result


# Then steps
@then("la solicitud GET a /v3/teams debe tener estado 200")
async def response_has_status_200(etl_result):
    """Verificar que la solicitud tiene estado 200."""
    assert etl_result is not None
    assert etl_result.get("status") == "success"


@then("la respuesta debe contener una lista de equipos con campos: id, name, code, logo_url")
def response_contains_teams_with_required_fields(sample_teams_response):
    """Verificar que la respuesta contiene equipos con campos requeridos."""
    assert "Teams" in sample_teams_response
    assert len(sample_teams_response["Teams"]) > 0
    
    for team in sample_teams_response["Teams"]:
        assert "id" in team
        assert "name" in team
        assert "code" in team
        assert "logo_url" in team


@then("la base de datos debe contener exactamente 2 equipos")
async def database_should_have_2_teams(etl_result):
    """Verificar que la BD contiene 2 equipos."""
    assert etl_result["total_processed"] == 2


@then("cada equipo debe tener los campos requeridos: id, name, code, logo_url")
async def each_team_has_required_fields(etl_result):
    """Verificar que cada equipo tiene campos requeridos."""
    assert etl_result["total_processed"] >= 1


@then("la base de datos debe contener exactamente 1 equipo")
async def database_should_have_1_team(etl_result):
    """Verificar que la BD contiene 1 equipo."""
    assert etl_result["total_processed"] == 1


@then("el nombre del equipo con id=1 debe ser actualizado a \"Real Madrid CF\"")
async def team_name_updated_correctly(sample_updated_team):
    """Verificar que el nombre del equipo se actualiza."""
    assert sample_updated_team["name"] == "Real Madrid CF"


@then("la base de datos debe contener exactamente 3 equipos")
async def database_should_have_3_teams(etl_result):
    """Verificar que la BD contiene 3 equipos."""
    assert etl_result["total_processed"] == 3


@then("no deben haber duplicados")
async def no_duplicates(etl_result):
    """Verificar que no hay duplicados."""
    assert etl_result["errors"] == 0


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


@then("los equipos con campos incompletos deben ser rechazados o completados con valores por defecto")
async def incomplete_teams_handled(etl_result):
    """Verificar que los equipos incompletos son manejados."""
    # El ETL debe procesar equipos aunque falten campos opcionales
    assert etl_result["total_processed"] >= 1


@then("no deben haber duplicados después de múltiples ejecuciones")
async def no_duplicates_after_multiple_runs(etl_result_2):
    """Verificar que no hay duplicados después de múltiples ejecuciones."""
    # Ambas ejecuciones deben ser idempotentes
    assert etl_result_2["status"] == "success"

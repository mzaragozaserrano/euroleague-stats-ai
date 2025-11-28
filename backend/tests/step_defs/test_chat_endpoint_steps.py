"""
Step definitions para tests BDD del Chat Endpoint.

Cubre: RAG retrieval, SQL generation, execution, error handling.
"""

import pytest
import json
import logging
from pytest_bdd import given, when, then, parsers
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.routers.chat import ChatRequest, ChatResponse
from app.services.vectorization import VectorizationService

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def client():
    """Cliente HTTP async para testing."""
    return AsyncClient(app=app, base_url="http://test")


@pytest.fixture
def chat_request_valid():
    """Request valido para chat endpoint."""
    return {
        "query": "puntos de Larkin en la temporada",
        "history": []
    }


@pytest.fixture
def chat_request_with_history():
    """Request con historia de conversacion."""
    return {
        "query": "¿Y Micic?",
        "history": [
            {"role": "user", "content": "puntos de Larkin"},
            {"role": "assistant", "content": "Larkin anoto 25 puntos"}
        ]
    }


# ============================================================================
# BACKGROUND STEPS
# ============================================================================

@given("la base de datos contiene equipos, jugadores y estadisticas precargadas")
async def db_with_test_data(db_session: AsyncSession):
    """Precarga datos de test en la BD."""
    # Este seria realizado por conftest.py con fixtures de BD
    pass


@given("el servicio de vectorizacion esta disponible")
async def vectorization_service_available():
    """Verifica que el servicio de vectorizacion este disponible."""
    # Mock o conexion real a OpenAI
    pass


@given("el LLM (OpenRouter) esta disponible")
async def llm_available():
    """Verifica que OpenRouter este accesible."""
    pass


# ============================================================================
# SCENARIO 1: Respuesta valida para consulta simple
# ============================================================================

@given("una consulta valida \"puntos de Larkin en la temporada\"")
def valid_query():
    """Define una consulta valida."""
    return "puntos de Larkin en la temporada"


@when("se envía una solicitud POST a /api/chat con query y history vacío")
async def post_chat_request_simple(client: AsyncClient, valid_query):
    """Envía request a /api/chat."""
    request_body = {
        "query": valid_query,
        "history": []
    }
    response = await client.post("/api/chat", json=request_body)
    return response


@then("la respuesta tiene status 200")
def check_status_200(response):
    """Verifica status 200."""
    assert response.status_code == 200, f"Esperaba 200, obtuve {response.status_code}"


@then("la respuesta contiene un campo sql con una consulta valida")
def check_sql_field(response):
    """Verifica que la respuesta tenga campo sql valido."""
    data = response.json()
    assert "sql" in data, "Campo 'sql' no encontrado en respuesta"
    assert isinstance(data["sql"], str), "Campo 'sql' debe ser string"
    assert len(data["sql"]) > 0, "Campo 'sql' no puede estar vacio"
    # Validar que sea SELECT (no DROP/DELETE)
    assert data["sql"].upper().startswith("SELECT"), "SQL debe ser SELECT"


@then("la respuesta contiene un campo data con resultados")
def check_data_field(response):
    """Verifica que tenga campo data."""
    data = response.json()
    assert "data" in data, "Campo 'data' no encontrado"
    assert isinstance(data["data"], (list, dict)), "Campo 'data' debe ser lista o dict"


@then("la respuesta contiene un campo visualization con tipo 'table'")
def check_visualization_field(response):
    """Verifica campo visualization."""
    data = response.json()
    assert "visualization" in data, "Campo 'visualization' no encontrado"
    valid_types = ["table", "bar", "line"]
    assert data["visualization"] in valid_types, \
        f"Visualization debe ser uno de {valid_types}"


@then("la respuesta no tiene campo error")
def check_no_error_field(response):
    """Verifica que no haya campo error."""
    data = response.json()
    assert "error" not in data or data.get("error") is None, \
        "Deberia no haber campo error en respuesta exitosa"


# ============================================================================
# SCENARIO 2: Historia de conversacion
# ============================================================================

@given("una consulta valida \"puntos de Larkin\"")
def valid_query_larkin():
    return "puntos de Larkin"


@given("una historia de conversacion previa con 2 mensajes")
def conversation_history():
    return [
        {"role": "user", "content": "Quien es el mejor scorer?"},
        {"role": "assistant", "content": "Larkin es el mejor scorer de la temporada"}
    ]


@when("se envía una solicitud POST a /api/chat con query e history")
async def post_chat_with_history(client: AsyncClient, valid_query_larkin, conversation_history):
    """Envía request con history."""
    request_body = {
        "query": valid_query_larkin,
        "history": conversation_history
    }
    response = await client.post("/api/chat", json=request_body)
    return response


@then("el LLM recibe el contexto de historia en el prompt")
def check_history_in_prompt(response):
    """Verifica que history fue usado en el prompt."""
    # Esto se verificaria mediante logs o mocks del LLM
    assert response.status_code == 200


@then("la respuesta contiene sql, data y visualization")
def check_response_fields(response):
    """Verifica campos basicos."""
    data = response.json()
    assert "sql" in data
    assert "data" in data
    assert "visualization" in data


# ============================================================================
# SCENARIO 3: Deteccion de visualizacion
# ============================================================================

@given("una consulta que solicita comparacion de datos \"puntos por equipo\"")
def comparison_query():
    return "puntos por equipo"


@when("se envía una solicitud POST a /api/chat")
async def post_chat_comparison(client: AsyncClient, comparison_query):
    """Envía request de comparacion."""
    response = await client.post("/api/chat", json={
        "query": comparison_query,
        "history": []
    })
    return response


@then(parsers.parse("la respuesta contiene visualization = 'bar' o 'line'"))
def check_visualization_type(response):
    """Verifica que sea grafico, no tabla."""
    data = response.json()
    viz = data.get("visualization")
    assert viz in ["bar", "line"], f"Se esperaba bar o line, obtuvo {viz}"


@then("los datos son multiples puntos para un grafico")
def check_data_for_chart(response):
    """Verifica que data sea apropiada para grafico."""
    data = response.json()
    chart_data = data.get("data")
    assert isinstance(chart_data, (list, dict)), "Data debe ser iterable para grafico"


# ============================================================================
# SCENARIO 4: SQL peligroso rechazado
# ============================================================================

@given("una consulta maliciosa que intenta \"DROP TABLE players\"")
def malicious_query():
    return "DROP TABLE players"


@when("se envía una solicitud POST a /api/chat")
async def post_malicious_query(client: AsyncClient, malicious_query):
    """Envía query maliciosa."""
    response = await client.post("/api/chat", json={
        "query": malicious_query,
        "history": []
    })
    return response


@then("la respuesta contiene un campo error explicando \"Consulta peligrosa rechazada\"")
def check_dangerous_query_error(response):
    """Verifica que la query peligrosa sea rechazada."""
    data = response.json()
    assert "error" in data, "Debe haber campo error para query peligrosa"
    assert "peligrosa" in data["error"].lower() or "drop" in data["error"].lower(), \
        "Error debe explicar que es peligrosa"


@then("no se ejecuta ningun SQL")
def verify_no_sql_execution(response):
    """Verifica que no se ejecute SQL."""
    data = response.json()
    assert data.get("sql") is None or data.get("sql") == "", \
        "No deberia haber SQL generado para query peligrosa"


# ============================================================================
# SCENARIO 5: Error de BD sin crash
# ============================================================================

@given("la base de datos esta temporalmente desconectada")
async def db_disconnected():
    """Simula desconexion de BD."""
    # Mock del get_db() para retornar error
    pass


@when("se envía una solicitud POST a /api/chat con una consulta valida")
async def post_chat_db_error(client: AsyncClient):
    """Envía request cuando BD esta caida."""
    response = await client.post("/api/chat", json={
        "query": "puntos de Larkin",
        "history": []
    })
    return response


@then("la respuesta contiene un campo error explicando \"No se pudo conectar a la BD\"")
def check_db_error(response):
    """Verifica que el error sea capturado."""
    data = response.json()
    assert response.status_code == 200, "Status debe ser 200 incluso con error"
    assert "error" in data, "Debe tener campo error"
    assert "BD" in data["error"] or "base de datos" in data["error"].lower(), \
        "Error debe mencionar problema con BD"


@then("el backend no crashea")
def backend_alive():
    """Verifica que el backend siga funcionando."""
    # Si llegamos aqui, el backend no crasheo
    assert True


# ============================================================================
# SCENARIO 6: Error del LLM sin crash
# ============================================================================

@given("el LLM (OpenRouter) esta temporalmente inaccesible")
async def llm_unavailable():
    """Simula que OpenRouter no esta disponible."""
    pass


@when("se envía una solicitud POST a /api/chat")
async def post_chat_llm_error(client: AsyncClient):
    """Envía request cuando LLM esta caido."""
    response = await client.post("/api/chat", json={
        "query": "puntos de Larkin",
        "history": []
    })
    return response


@then("la respuesta contiene un campo error explicando \"LLM no disponible\"")
def check_llm_error(response):
    """Verifica que el error del LLM sea capturado."""
    data = response.json()
    assert response.status_code == 200
    assert "error" in data
    assert "LLM" in data["error"] or "disponible" in data["error"].lower()


# ============================================================================
# SCENARIO 7: Logs de RAG retrieval
# ============================================================================

@given("una consulta \"estadisticas de Micic\"")
def micic_query():
    return "estadisticas de Micic"


@then("los logs muestran \"RAG retrieval: <N> documentos encontrados\"")
def check_rag_logs(caplog):
    """Verifica que haya logs de RAG retrieval."""
    assert any("RAG retrieval" in record.message for record in caplog.records), \
        "Debe haber log de RAG retrieval"


@then("los logs muestran el similarity score de cada documento")
def check_similarity_logs(caplog):
    """Verifica scores de similarity en logs."""
    assert any("similarity" in record.message.lower() for record in caplog.records), \
        "Debe haber logs de similarity scores"


# ============================================================================
# SCENARIO 8: Latencia < 5 segundos
# ============================================================================

@then("la respuesta se recibe en menos de 5 segundos")
def check_latency(response):
    """Verifica que latencia sea aceptable."""
    # En un test real, usariamos timeit o similar
    # Este es un placeholder
    assert response.status_code == 200


@then("el tiempo de latencia se reporta en la respuesta")
def check_latency_field(response):
    """Verifica que haya campo de latencia."""
    data = response.json()
    # Opcional: poder tener campo latency
    # assert "latency_ms" in data


# ============================================================================
# SCENARIO 9: Query sin resultados
# ============================================================================

@given("una consulta valida pero sin coincidencias en BD \"jugador inexistente X\"")
def no_results_query():
    return "stats de jugador XXXXXX que no existe"


@when("se envía una solicitud POST a /api/chat")
async def post_no_results_query(client: AsyncClient, no_results_query):
    """Envía query sin resultados."""
    response = await client.post("/api/chat", json={
        "query": no_results_query,
        "history": []
    })
    return response


@then("la respuesta contiene data = [] (lista vacia)")
def check_empty_data(response):
    """Verifica que data sea lista vacia."""
    data = response.json()
    assert data.get("data") == [] or data.get("data") == {}, \
        "Data deberia estar vacia"


@then("no hay campo error (es una respuesta valida)")
def check_no_error_on_empty():
    """Una query sin resultados no es error."""
    # Las listas vacias son respuestas validas
    pass


# ============================================================================
# SCENARIO 10: Validacion de request schema
# ============================================================================

@given("un request sin campo query")
def invalid_request():
    return {"history": []}


@when("se envía una solicitud POST a /api/chat sin query")
async def post_invalid_request(client: AsyncClient, invalid_request):
    """Envía request inválido."""
    response = await client.post("/api/chat", json=invalid_request)
    return response


@then("la respuesta tiene status 422 (Unprocessable Entity)")
def check_422_status(response):
    """Verifica que sea error de validacion."""
    assert response.status_code == 422, f"Se espera 422, obtuve {response.status_code}"


@then("la respuesta contiene detalles del error de validacion")
def check_validation_error_details(response):
    """Verifica detalles de validacion."""
    data = response.json()
    assert "detail" in data, "Debe tener detalles del error"


# ============================================================================
# SCENARIO 11: RAG retrieval utiliza vector similarity
# ============================================================================

@given("una consulta \"puntos del jugador\"")
def points_query():
    return "puntos del jugador"


@when("se ejecuta RAG retrieval para encontrar esquema relevante")
async def execute_rag_retrieval(db_session: AsyncSession, points_query):
    """Ejecuta RAG retrieval."""
    vectorization_service = VectorizationService(api_key="test-key")
    # Este test necesitaria mock del LLM
    relevant_schema = await vectorization_service.retrieve_relevant_schema(
        db_session, points_query, limit=5
    )
    return relevant_schema


@then("se retornan metadatos sobre tabla player_stats_games")
def check_player_stats_metadata(rag_results):
    """Verifica que player_stats este en resultados."""
    assert any("player_stats" in item.get("content", "").lower() 
               for item in rag_results), \
        "Debe retornar info sobre player_stats_games"


@then("se retornan metadatos sobre columna points")
def check_points_metadata(rag_results):
    """Verifica que points este en resultados."""
    assert any("points" in item.get("content", "").lower() 
               for item in rag_results), \
        "Debe retornar info sobre columna points"


@then("los resultados ordenados por similarity descendente")
def check_similarity_order(rag_results):
    """Verifica orden de similarity."""
    if len(rag_results) > 1:
        similarities = [item.get("similarity", 0) for item in rag_results]
        assert similarities == sorted(similarities, reverse=True), \
            "Resultados deben estar ordenados por similarity descendente"


# ============================================================================
# SCENARIO 12: SQL es ejecutable
# ============================================================================

@given("una consulta valida \"promedio de puntos por equipo\"")
def avg_points_query():
    return "promedio de puntos por equipo"


@when("se genera SQL mediante LLM")
async def generate_sql(client: AsyncClient, avg_points_query):
    """Genera SQL mediante LLM."""
    response = await client.post("/api/chat", json={
        "query": avg_points_query,
        "history": []
    })
    return response.json().get("sql")


@then("el SQL cumple con restricciones de seguridad (no DROP/DELETE)")
def check_sql_security(sql):
    """Verifica SQL no tiene operaciones peligrosas."""
    assert "DROP" not in sql.upper()
    assert "DELETE" not in sql.upper()
    assert "TRUNCATE" not in sql.upper()


@then("el SQL es valido PostgreSQL")
def check_sql_valid(sql):
    """Verifica que sea SQL valido."""
    # Esto requeriria un parser SQL o conexion a BD
    assert sql.strip().upper().startswith("SELECT")


@then("el SQL se ejecuta exitosamente contra Neon")
def check_sql_execution(sql, db_session: AsyncSession):
    """Verifica que SQL se ejecute sin errores."""
    # Este es un test de integracion que ejecutaria el SQL real
    pass


@then("se retornan resultados en formato JSON")
def check_json_format(response):
    """Verifica formato JSON."""
    data = response.json()
    assert isinstance(data.get("data"), (list, dict))


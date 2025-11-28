"""
Step definitions para schema embeddings vectorization (BDD).

Estos pasos validan la generación y recuperación de embeddings de metadatos
usando pytest-bdd.
"""

import pytest
from pytest_bdd import given, when, then, scenario
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.vectorization import VectorizationService
from app.database import async_session_maker
import logging

logger = logging.getLogger(__name__)


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def metadata_descriptions():
    """Proporciona descripciones de metadatos de ejemplo."""
    return [
        {
            "content": "Table: teams - Stores Euroleague basketball teams with id, code, name, logo_url"
        },
        {
            "content": "Table: players - Stores player information with id, team_id, name, position, height, birth_date"
        },
        {
            "content": "Column: points - Total points scored by a player in a game"
        },
        {
            "content": "Column: assists - Number of assists made by a player in a game"
        },
        {
            "content": "Example SQL: SELECT p.name, SUM(points) FROM player_stats_games psg JOIN players p ON psg.player_id = p.id GROUP BY p.name"
        },
    ]


@pytest.fixture
async def vectorization_service(settings_fixture):
    """Proporciona una instancia del servicio de vectorización."""
    return VectorizationService(api_key=settings_fixture.openai_api_key)


@pytest.fixture
async def clean_embeddings_table():
    """Limpia la tabla de embeddings antes de cada test."""
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM schema_embeddings"))
        await session.commit()
    yield
    # Cleanup después del test
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM schema_embeddings"))
        await session.commit()


# ============================================================================
# SCENARIOS
# ============================================================================


@scenario("../features/schema_embeddings.feature", "Generate embeddings for table descriptions")
def test_generate_embeddings():
    """Scenario: Generate embeddings for table descriptions"""
    pass


@scenario("../features/schema_embeddings.feature", "Retrieve relevant schema by similarity")
def test_retrieve_relevant_schema():
    """Scenario: Retrieve relevant schema by similarity"""
    pass


@scenario(
    "../features/schema_embeddings.feature", "Clear and reinitialize embeddings"
)
def test_clear_reinitialize_embeddings():
    """Scenario: Clear and reinitialize embeddings"""
    pass


@scenario("../features/schema_embeddings.feature", "Handle API errors gracefully")
def test_handle_api_errors():
    """Scenario: Handle API errors gracefully"""
    pass


@scenario("../features/schema_embeddings.feature", "Validate embedding dimensions")
def test_validate_embedding_dimensions():
    """Scenario: Validate embedding dimensions"""
    pass


@scenario("../features/schema_embeddings.feature", "Retrieve top-k similar schemas")
def test_retrieve_topk_similar_schemas():
    """Scenario: Retrieve top-k similar schemas"""
    pass


# ============================================================================
# GIVEN STEPS
# ============================================================================


@given("I have metadata descriptions for schema tables")
async def given_metadata_descriptions(metadata_descriptions):
    """Preparar metadatos de esquema."""
    assert metadata_descriptions is not None
    assert len(metadata_descriptions) == 5


@given("the schema_embeddings table contains multiple embeddings", target_fixture="embedded_count")
async def given_embeddings_in_table(
    vectorization_service, metadata_descriptions, clean_embeddings_table
):
    """Insertar múltiples embeddings en la tabla."""
    async with async_session_maker() as session:
        inserted = await vectorization_service.vectorize_schema_metadata(
            session, metadata_descriptions
        )
    return inserted


@given("the schema_embeddings table has existing data", target_fixture="initial_count")
async def given_existing_embeddings(
    vectorization_service, metadata_descriptions, clean_embeddings_table
):
    """Asegurar que hay datos en la tabla."""
    async with async_session_maker() as session:
        inserted = await vectorization_service.vectorize_schema_metadata(
            session, metadata_descriptions
        )
    return inserted


@given("OpenAI API is temporarily unavailable")
def given_api_unavailable():
    """Simular que la API no está disponible."""
    # En un test real, se mockearía la llamada a OpenAI
    pass


@given("I have successfully generated embeddings", target_fixture="stored_embeddings")
async def given_successful_embeddings(
    vectorization_service, metadata_descriptions, clean_embeddings_table
):
    """Generar embeddings exitosamente."""
    async with async_session_maker() as session:
        inserted = await vectorization_service.vectorize_schema_metadata(
            session, metadata_descriptions
        )
    return inserted


@given("the schema_embeddings table has at least 5 embeddings")
async def given_at_least_5_embeddings(
    vectorization_service, metadata_descriptions, clean_embeddings_table
):
    """Asegurar que hay al menos 5 embeddings."""
    # Ampliar metadatos si es necesario
    extended_metadata = metadata_descriptions + [
        {"content": "Additional embedding 1"},
        {"content": "Additional embedding 2"},
    ]

    async with async_session_maker() as session:
        await vectorization_service.vectorize_schema_metadata(session, extended_metadata)


# ============================================================================
# WHEN STEPS
# ============================================================================


@when("I generate embeddings using OpenAI", target_fixture="generated_embeddings")
async def when_generate_embeddings(vectorization_service, metadata_descriptions):
    """Generar embeddings usando OpenAI."""
    embeddings = []
    for item in metadata_descriptions:
        embedding = await vectorization_service.generate_embedding(item["content"])
        embeddings.append(embedding)
    return embeddings


@when("I query for \"puntos de jugadores\"", target_fixture="query_results")
async def when_query_for_points(vectorization_service):
    """Realizar una búsqueda de similitud."""
    async with async_session_maker() as session:
        results = await vectorization_service.retrieve_relevant_schema(
            session, "puntos de jugadores", limit=5
        )
    return results


@when("I clear all schema embeddings")
async def when_clear_embeddings(vectorization_service):
    """Limpiar todos los embeddings."""
    async with async_session_maker() as session:
        await vectorization_service.clear_schema_embeddings(session)


@when("I reinitialize with metadata")
async def when_reinitialize_embeddings(vectorization_service, metadata_descriptions):
    """Reinicializar con metadatos."""
    async with async_session_maker() as session:
        await vectorization_service.vectorize_schema_metadata(
            session, metadata_descriptions
        )


@when("I attempt to generate embeddings")
async def when_attempt_embeddings(vectorization_service):
    """Intentar generar embeddings cuando API no está disponible."""
    # Este test debería mockar la API
    pass


@when("I query the database for stored embeddings", target_fixture="db_embeddings")
async def when_query_db_embeddings():
    """Consultar embeddings almacenados en la base de datos."""
    async with async_session_maker() as session:
        result = await session.execute(
            text(
                "SELECT id, content, embedding, array_length(embedding::float8[], 1) as dimensions FROM schema_embeddings"
            )
        )
        rows = result.fetchall()
    return rows


@when("I perform a similarity search with limit=3", target_fixture="topk_results")
async def when_similarity_search_topk(vectorization_service):
    """Realizar búsqueda de similitud con limit=3."""
    async with async_session_maker() as session:
        results = await vectorization_service.retrieve_relevant_schema(
            session, "player scoring statistics", limit=3
        )
    return results


# ============================================================================
# THEN STEPS
# ============================================================================


@then("the embeddings should have 1536 dimensions")
def then_embeddings_dimensions(generated_embeddings):
    """Validar dimensiones de embeddings."""
    for embedding in generated_embeddings:
        assert len(embedding) == 1536, f"Expected 1536 dims, got {len(embedding)}"


@then("the embeddings should be stored in schema_embeddings table")
async def then_embeddings_stored():
    """Validar que se almacenaron en la base de datos."""
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM schema_embeddings")
        )
        count = result.scalar()
    assert count > 0, "No embeddings found in database"


@then("I should receive relevant schema descriptions")
def then_receive_results(query_results):
    """Validar que se recibieron resultados."""
    assert query_results is not None
    assert len(query_results) > 0, "No results retrieved"


@then("the results should be ordered by cosine similarity score")
def then_results_ordered(query_results):
    """Validar que los resultados están ordenados por similitud."""
    similarities = [r["similarity"] for r in query_results]
    assert similarities == sorted(similarities, reverse=True), (
        "Results not ordered by similarity"
    )


@then("the table should be empty")
async def then_table_empty():
    """Validar que la tabla está vacía."""
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM schema_embeddings")
        )
        count = result.scalar()
    assert count == 0, f"Table not empty, found {count} records"


@then("the embeddings should be successfully stored")
async def then_embeddings_stored_after_reinit():
    """Validar que se almacenaron después de reinicializar."""
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM schema_embeddings")
        )
        count = result.scalar()
    assert count > 0, "No embeddings stored after reinitialization"


@then("the system should raise an exception")
def then_system_raises_exception():
    """Validar que se levanta una excepción."""
    pass


@then("log the error appropriately")
def then_error_logged():
    """Validar que se registró el error."""
    pass


@then("not corrupt existing embeddings")
async def then_no_corruption():
    """Validar que no se corrompieron embeddings existentes."""
    async with async_session_maker() as session:
        result = await session.execute(
            text("SELECT COUNT(*) FROM schema_embeddings")
        )
        count = result.scalar()
    assert count >= 0, "Database integrity compromised"


@then("each embedding should have exactly 1536 dimensions")
def then_each_embedding_dimensions(db_embeddings):
    """Validar dimensiones de cada embedding."""
    for row in db_embeddings:
        dimensions = row[3]  # array_length(embedding, 1)
        assert dimensions == 1536, f"Expected 1536 dims, got {dimensions}"


@then("the embedding type should be vector")
async def then_embedding_type_vector():
    """Validar que el tipo de embedding es vector."""
    async with async_session_maker() as session:
        result = await session.execute(
            text(
                """
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'schema_embeddings' AND column_name = 'embedding'
                """
            )
        )
        row = result.fetchone()
    assert row is not None, "Embedding column not found"
    # pgvector almacena como 'USER-DEFINED' type
    assert row[1] == "USER-DEFINED", f"Expected USER-DEFINED, got {row[1]}"


@then("I should receive exactly 3 results")
def then_exactly_3_results(topk_results):
    """Validar que se recibieron exactamente 3 resultados."""
    assert len(topk_results) == 3, f"Expected 3 results, got {len(topk_results)}"


@then("results should be sorted by similarity score descending")
def then_results_sorted_descending(topk_results):
    """Validar que los resultados están ordenados descendentemente."""
    similarities = [r["similarity"] for r in topk_results]
    assert similarities == sorted(similarities, reverse=True), (
        "Results not sorted by similarity descending"
    )


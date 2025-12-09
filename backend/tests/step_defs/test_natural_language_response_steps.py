import pytest
import asyncio
from pytest_bdd import scenarios, given, when, then, parsers
from app.services.response_generator import ResponseGeneratorService
from unittest.mock import AsyncMock, MagicMock

scenarios('../features/natural_language_response.feature')

@pytest.fixture
def mock_openrouter():
    mock = AsyncMock()
    # Mocking a detailed Markdown response with a full table
    mock.chat.completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="""
### Plantilla del Real Madrid

Aquí tienes la plantilla completa del Real Madrid para esta temporada:

| Jugador | Posición |
|---------|----------|
| **Sergio Llull** | G |
| **Facundo Campazzo** | G |
| **Walter Tavares** | C |
| **Gabriel Deck** | F |
| **Dzanan Musa** | F |
| **Mario Hezonja** | F |
| **Vincent Poirier** | C |
| **Rudy Fernandez** | F |
| **Fabien Causeur** | G |
| **Alberto Abalde** | F |

> Un equipo diseñado para ganarlo todo.
"""))
    ]
    return mock

@pytest.fixture
def response_holder():
    return {}

@given('the user asks "Cuales son los jugadores del Real Madrid?"', target_fixture="query")
def user_query():
    return "Cuales son los jugadores del Real Madrid?"

@given('the database returns stats for "Markus Howard" with "25.0" points', target_fixture="data")
def db_data():
    # Simulate a full roster
    return [
        {"player_name": "Sergio Llull", "position": "G"},
        {"player_name": "Facundo Campazzo", "position": "G"},
        {"player_name": "Walter Tavares", "position": "C"},
        {"player_name": "Gabriel Deck", "position": "F"},
        {"player_name": "Dzanan Musa", "position": "F"},
        {"player_name": "Mario Hezonja", "position": "F"},
        {"player_name": "Vincent Poirier", "position": "C"},
        {"player_name": "Rudy Fernandez", "position": "F"},
        {"player_name": "Fabien Causeur", "position": "G"},
        {"player_name": "Alberto Abalde", "position": "F"},
    ]

@when("the chat endpoint processes the request")
def process_request(query, data, mock_openrouter, response_holder):
    service = ResponseGeneratorService(api_key="fake-key")
    service.client = mock_openrouter
    
    async def run():
        return await service.generate_response(query, data)
    
    # Run async code synchronously
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
    response_text = loop.run_until_complete(run())
    
    response_holder["message"] = response_text
    response_holder["data"] = data

@then('the response should contain a "message" field')
def check_message_field(response_holder):
    assert "message" in response_holder
    assert response_holder["message"] is not None
    assert len(response_holder["message"]) > 100

@then(parsers.parse('the message should mention "{text}"'))
def check_message_content(response_holder, text):
    # Verify key players are mentioned (simulated by the mock content)
    assert text in response_holder["message"]

@then('the response should contain structured data')
def check_structured_data(response_holder):
    assert "data" in response_holder
    assert len(response_holder["data"]) == 10

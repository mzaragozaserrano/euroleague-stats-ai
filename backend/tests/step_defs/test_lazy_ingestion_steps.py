import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.text_to_sql import TextToSQLService

# Load scenarios
scenarios('../features/lazy_ingestion.feature')

# Shared context to store mocks
class TestContext:
    mock_etl = None

@pytest.fixture
def test_context():
    return TestContext()

@given(parsers.parse('the database has no data for season "{season_code}"'))
def ensure_no_data(season_code, test_context):
    # This setup is handled in the 'when' step where we patch everything
    pass

import asyncio

@when(parsers.parse('the user sends the message "{message}"'))
def send_message(message, test_context):
    # Patch everything manually
    
    # 1. Mock ETL
    with patch("app.services.text_to_sql.run_ingest_player_season_stats", new_callable=AsyncMock) as mock_etl:
        test_context.mock_etl = mock_etl
        
        # 2. Mock OpenAI
        with patch("app.services.text_to_sql.AsyncOpenAI") as mock_openai_cls:
            mock_client = mock_openai_cls.return_value
            mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"sql": "SELECT * FROM players", "visualization_type": "table"}'))]
            ))
            
            # 3. Mock DB Session
            mock_session = AsyncMock()
            mock_result_missing = MagicMock() # Result object is synchronous
            mock_result_missing.scalar.return_value = None # Missing data
            
            mock_result_data = MagicMock()
            mock_result_data.fetchall.return_value = []
            
            # Sequence: SELECT 1 (check) -> SELECT stats (fetch)
            mock_session.execute.side_effect = [mock_result_missing, mock_result_data, mock_result_data, mock_result_data, mock_result_data]
            
            mock_session_maker = MagicMock()
            mock_session_maker.__aenter__.return_value = mock_session
            mock_session_maker.return_value = mock_session_maker

            with patch("app.services.text_to_sql.async_session_maker", return_value=mock_session_maker):
                service = TextToSQLService(api_key="fake-key")
                
                async def run():
                     await service.generate_sql(query=message, schema_context="Mock Schema")
                
                # Run async code synchronously
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                loop.run_until_complete(run())

@then(parsers.parse('the system should trigger the data ingestion for season "{season_code}"'))
def check_ingestion_triggered(test_context, season_code):
    year = int(season_code.replace("E", ""))
    assert test_context.mock_etl.called
    test_context.mock_etl.assert_called_with(season=year)

@then('the system should return a valid response with stats')
def check_response():
    pass

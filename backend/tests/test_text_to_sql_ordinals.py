import pytest

from app.services.text_to_sql import TextToSQLService


@pytest.mark.asyncio
async def test_detects_ordinal_best_fourth():
    service = TextToSQLService(api_key="test")
    info = service._detect_comparison_with_maximum("Compara a Pep con el cuarto maximo anotador")
    assert info is not None
    assert info["rank"] == 4
    assert info["direction"] == "desc"
    assert info["stat"] == "points"


@pytest.mark.asyncio
async def test_detects_second_worst_rebounder():
    service = TextToSQLService(api_key="test")
    info = service._detect_comparison_with_maximum("Compara a Pep con el segundo peor reboteador")
    assert info is not None
    assert info["rank"] == 2
    assert info["direction"] == "asc"
    assert info["stat"] == "rebounds"


@pytest.mark.asyncio
async def test_detects_second_best_assistant_word_ordinal():
    service = TextToSQLService(api_key="test")
    info = service._detect_comparison_with_maximum("Compara a Pep con el segundo mejor asistente")
    assert info is not None
    assert info["rank"] == 2
    assert info["direction"] == "desc"
    assert info["stat"] == "assists"


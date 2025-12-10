import pytest

from app.services.response_generator import ResponseGeneratorService


def test_maximum_disambiguation_uses_leader_from_data():
    service = ResponseGeneratorService(api_key="test")
    data = [
        {"player": "Campazzo", "assists": 95.0},
        {"player": "Sylvain", "assists": 102.0},
    ]
    query = "Compara a Campazzo con el maximo asistente"

    stat_column = service._detect_stat_column(query, data)
    player_column = service._detect_player_column(data)
    maximum_context = service._build_maximum_disambiguation(query, data, stat_column, player_column)

    assert maximum_context != ""
    assert "Sylvain" in maximum_context
    assert "Campazzo: 95.0" in maximum_context
    assert "jugador->valor" in maximum_context


def test_maximum_disambiguation_ignores_non_max_queries():
    service = ResponseGeneratorService(api_key="test")
    data = [
        {"player": "Campazzo", "assists": 95.0},
        {"player": "Sylvain", "assists": 102.0},
    ]
    query = "Compara a Campazzo con Sylvain"

    stat_column = service._detect_stat_column(query, data)
    player_column = service._detect_player_column(data)
    maximum_context = service._build_maximum_disambiguation(query, data, stat_column, player_column)

    assert maximum_context == ""


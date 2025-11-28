"""
Módulo ETL para la ingesta de datos desde la API de Euroleague.
"""

from etl.euroleague_client import (
    EuroleagueClient,
    EuroleagueClientError,
    EuroleagueAPIError,
    EuroleagueRateLimitError,
    EuroleagueTimeoutError,
)

__all__ = [
    "EuroleagueClient",
    "EuroleagueClientError",
    "EuroleagueAPIError",
    "EuroleagueRateLimitError",
    "EuroleagueTimeoutError",
]


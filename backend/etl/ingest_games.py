"""
Script ETL para estadísticas de jugadores (DESHABILITADO PARA MVP).

NOTA IMPORTANTE:
Este módulo está deshabilitado para el MVP. Las estadísticas de jugadores
se obtienen en tiempo real desde la API de Euroleague usando PlayerStatsService
con caché Redis (TTL 24h).

Arquitectura actual:
- BD: Solo equipos + jugadores (roster)
- Redis: Caché de stats por temporada (24h)
- API: Llamadas dinámicas cuando se necesita

Ver: backend/app/services/player_stats_service.py
"""

import logging

logger = logging.getLogger(__name__)


async def main():
    """Punto de entrada (deshabilitado)."""
    logger.warning("=" * 80)
    logger.warning("MÓDULO DESHABILITADO PARA MVP")
    logger.warning("=" * 80)
    logger.warning("")
    logger.warning("Las estadísticas de jugadores se obtienen en tiempo real")
    logger.warning("usando PlayerStatsService con caché Redis.")
    logger.warning("")
    logger.warning("Ver: backend/app/services/player_stats_service.py")
    logger.warning("=" * 80)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())

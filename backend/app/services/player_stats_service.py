"""
Servicio para obtener estadísticas de jugadores desde la API de Euroleague.

Implementa caché inteligente con Redis:
- Primera consulta del día: Llama API para todos los jugadores de una temporada
- Consultas subsecuentes: Usa caché (TTL 24h)
- Por temporada: Caché independiente (E2025, E2024, etc)

Flujo:
1. Usuario: "Top 10 anotadores 2025"
2. Service: ¿Cache hit E2025? NO → Llamar API 350 veces → Guardar caché
3. Usuario: "Top 10 reboteadores 2025"
4. Service: ¿Cache hit E2025? SÍ → Leer caché (instantáneo)
"""

import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime

import redis.asyncio as redis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Player
from app.database import async_session_maker
from app.config import settings
from etl.euroleague_client import EuroleagueClient, EuroleagueClientError

logger = logging.getLogger(__name__)

# Template de clave de caché: playerstats:{seasoncode}
CACHE_KEY_TEMPLATE = "playerstats:{seasoncode}"


class PlayerStatsServiceError(Exception):
    """Excepción base para errores del servicio de estadísticas."""

    pass


class PlayerStatsService:
    """
    Servicio para obtener y cachear estadísticas de jugadores.

    Atributos:
        redis_client: Cliente Redis para caché
        euroleague_client: Cliente de API Euroleague
        cache_ttl: Tiempo de vida del caché en segundos (default: 24h)
    """

    def __init__(self):
        """Inicializar servicio con clientes Redis y Euroleague."""
        self.redis_client: Optional[redis.Redis] = None
        self.euroleague_client = EuroleagueClient()
        self.cache_ttl = settings.redis_cache_ttl

    async def _get_redis_client(self) -> redis.Redis:
        """Obtener o crear cliente Redis."""
        if self.redis_client is None:
            self.redis_client = await redis.from_url(
                settings.redis_url, encoding="utf-8", decode_responses=True
            )
        return self.redis_client

    async def close(self):
        """Cerrar conexión Redis."""
        if self.redis_client:
            await self.redis_client.close()

    async def get_all_player_stats(self, seasoncode: str = "E2025") -> Dict[str, Any]:
        """
        Obtener estadísticas de TODOS los jugadores para una temporada.

        Usa caché si está disponible (TTL 24h), sino llama a la API de Euroleague
        para cada jugador registrado en la BD.

        Args:
            seasoncode: Código de temporada (ej: "E2025", "E2024")

        Returns:
            Diccionario con stats por jugador:
            {
                "DECK": {"points": 15.2, "assists": 3.1, ...},
                "PAU": {"points": 12.8, "rebounds": 6.2, ...},
                ...
            }

        Raises:
            PlayerStatsServiceError: Si hay error obteniendo stats
        """
        cache_key = CACHE_KEY_TEMPLATE.format(seasoncode=seasoncode)
        redis_client = await self._get_redis_client()

        try:
            # 1. Intentar obtener desde caché
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                logger.info(f"Cache HIT para {seasoncode}")
                return json.loads(cached_data)

            logger.info(f"Cache MISS para {seasoncode}. Llamando API de Euroleague...")

            # 2. Obtener códigos de jugadores desde BD
            player_codes = await self._get_player_codes_from_db()
            logger.info(f"Obteniendo stats para {len(player_codes)} jugadores...")

            # 3. Llamar API para cada jugador
            all_stats = await self._fetch_stats_from_api(seasoncode, player_codes)

            # 4. Guardar en caché por 24h
            await redis_client.setex(cache_key, self.cache_ttl, json.dumps(all_stats))
            logger.info(
                f"Stats guardadas en caché: {cache_key} (TTL: {self.cache_ttl}s / 24h)"
            )

            return all_stats

        except redis.RedisError as e:
            logger.error(f"Error de Redis: {str(e)}")
            # Si Redis falla, intentar obtener directamente de API sin caché
            logger.warning("Redis no disponible. Obteniendo stats sin caché...")
            player_codes = await self._get_player_codes_from_db()
            return await self._fetch_stats_from_api(seasoncode, player_codes)

        except Exception as e:
            logger.error(f"Error obteniendo stats: {str(e)}")
            raise PlayerStatsServiceError(f"Error obteniendo stats: {str(e)}") from e

    async def _get_player_codes_from_db(self) -> List[str]:
        """
        Obtener códigos de jugadores desde la base de datos.

        Returns:
            Lista de códigos de jugadores (ej: ["006590", "006591", ...])
        """
        async with async_session_maker() as session:
            stmt = select(Player.player_code).where(Player.player_code.isnot(None))
            result = await session.execute(stmt)
            player_codes = [row[0] for row in result.fetchall()]

        logger.debug(f"Obtenidos {len(player_codes)} códigos de jugadores de BD")
        return player_codes

    async def _fetch_stats_from_api(
        self, seasoncode: str, player_codes: List[str]
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas desde la API de Euroleague para múltiples jugadores.

        Args:
            seasoncode: Código de temporada (ej: "E2025")
            player_codes: Lista de códigos de jugadores

        Returns:
            Diccionario con stats por jugador
        """
        all_stats = {}
        total = len(player_codes)

        for idx, player_code in enumerate(player_codes, start=1):
            try:
                stats = await self.euroleague_client.get_playerstats(
                    seasoncode=seasoncode, playercode=player_code
                )
                all_stats[player_code] = stats

                # Log de progreso cada 50 jugadores
                if idx % 50 == 0:
                    logger.info(f"Progreso: {idx}/{total} jugadores procesados")

            except EuroleagueClientError as e:
                logger.warning(f"Error obteniendo stats para {player_code}: {str(e)}")
                all_stats[player_code] = None
            except Exception as e:
                logger.error(f"Error inesperado para {player_code}: {str(e)}")
                all_stats[player_code] = None

        logger.info(f"Stats obtenidas para {len(all_stats)}/{total} jugadores")
        return all_stats

    async def search_top_players(
        self,
        seasoncode: str = "E2025",
        stat: str = "points",
        top_n: int = 10,
        team_code: Optional[str] = None,
        min_value: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """
        Buscar top N jugadores por una estadística específica.

        Args:
            seasoncode: Código de temporada (ej: "E2025")
            stat: Estadística a ordenar (points, assists, rebounds, steals, blocks, etc)
            top_n: Número de jugadores a retornar
            team_code: Filtrar por código de equipo (opcional)
            min_value: Valor mínimo de la estadística (opcional)

        Returns:
            Lista de jugadores ordenados por la estadística:
            [
                {
                    "name": "Gabriel Deck",
                    "code": "DECK",
                    "team_id": 1,
                    "points": 15.2,
                    "all_stats": {...}
                },
                ...
            ]

        Raises:
            PlayerStatsServiceError: Si hay error en la búsqueda
        """
        try:
            # 1. Obtener todas las stats (desde caché o API)
            all_stats = await self.get_all_player_stats(seasoncode)

            # 2. Obtener datos de jugadores desde BD para enriquecer
            players_map = await self._get_players_map_from_db()

            # 3. Filtrar y procesar
            filtered_players = []

            for player_code, stats in all_stats.items():
                if stats is None:
                    continue

                player = players_map.get(player_code)
                if not player:
                    continue

                # Filtrar por equipo si se especifica
                if team_code and player.team_id != team_code:
                    continue

                # Obtener valor de la estadística
                stat_value = self._extract_stat_value(stats, stat)
                if stat_value is None:
                    continue

                # Filtrar por valor mínimo si se especifica
                if min_value is not None and stat_value < min_value:
                    continue

                filtered_players.append(
                    {
                        "name": player.name,
                        "code": player_code,
                        "team_id": player.team_id,
                        stat: stat_value,
                        "all_stats": stats,
                    }
                )

            # 4. Ordenar por estadística y obtener top N
            sorted_players = sorted(
                filtered_players, key=lambda x: x[stat], reverse=True
            )[:top_n]

            logger.info(
                f"Búsqueda completada: {len(sorted_players)} jugadores "
                f"(stat={stat}, season={seasoncode})"
            )

            return sorted_players

        except Exception as e:
            logger.error(f"Error en búsqueda de top players: {str(e)}")
            raise PlayerStatsServiceError(f"Error en búsqueda: {str(e)}") from e

    async def _get_players_map_from_db(self) -> Dict[str, Player]:
        """
        Obtener mapa de jugadores desde BD (player_code -> Player).

        Returns:
            Diccionario {player_code: Player}
        """
        async with async_session_maker() as session:
            stmt = select(Player).where(Player.player_code.isnot(None))
            result = await session.execute(stmt)
            players = result.scalars().all()

        players_map = {p.player_code: p for p in players}
        logger.debug(f"Obtenidos {len(players_map)} jugadores de BD")
        return players_map

    def _extract_stat_value(self, stats: Dict[str, Any], stat: str) -> Optional[float]:
        """
        Extraer valor de una estadística del diccionario de stats.

        Maneja diferentes formatos de respuesta de la API.

        Args:
            stats: Diccionario con estadísticas del jugador
            stat: Nombre de la estadística

        Returns:
            Valor numérico de la estadística o None
        """
        try:
            value = stats.get(stat)
            if value is None:
                return None
            return float(value)
        except (ValueError, TypeError):
            logger.warning(f"No se pudo convertir stat '{stat}' a float: {value}")
            return None

    async def clear_cache(self, seasoncode: Optional[str] = None):
        """
        Limpiar caché de estadísticas.

        Args:
            seasoncode: Si se especifica, limpia solo esa temporada.
                       Si es None, limpia todas las temporadas.
        """
        redis_client = await self._get_redis_client()

        try:
            if seasoncode:
                cache_key = CACHE_KEY_TEMPLATE.format(seasoncode=seasoncode)
                await redis_client.delete(cache_key)
                logger.info(f"Caché limpiada para {seasoncode}")
            else:
                # Limpiar todas las claves que coincidan con el patrón
                pattern = CACHE_KEY_TEMPLATE.format(seasoncode="*")
                keys = await redis_client.keys(pattern)
                if keys:
                    await redis_client.delete(*keys)
                    logger.info(f"Caché limpiada: {len(keys)} temporadas")
                else:
                    logger.info("No hay caché para limpiar")

        except redis.RedisError as e:
            logger.error(f"Error limpiando caché: {str(e)}")
            raise PlayerStatsServiceError(f"Error limpiando caché: {str(e)}") from e

    async def get_cache_info(self, seasoncode: str = "E2025") -> Dict[str, Any]:
        """
        Obtener información sobre el estado del caché.

        Args:
            seasoncode: Código de temporada

        Returns:
            Diccionario con info del caché:
            {
                "exists": bool,
                "ttl": int (segundos restantes),
                "size": int (bytes),
                "seasoncode": str
            }
        """
        redis_client = await self._get_redis_client()
        cache_key = CACHE_KEY_TEMPLATE.format(seasoncode=seasoncode)

        try:
            exists = await redis_client.exists(cache_key)
            ttl = await redis_client.ttl(cache_key) if exists else None

            info = {
                "exists": bool(exists),
                "ttl": ttl,
                "seasoncode": seasoncode,
                "cache_key": cache_key,
            }

            if exists:
                # Obtener tamaño aproximado
                cached_data = await redis_client.get(cache_key)
                info["size_bytes"] = len(cached_data) if cached_data else 0

            return info

        except redis.RedisError as e:
            logger.error(f"Error obteniendo info de caché: {str(e)}")
            return {
                "exists": False,
                "error": str(e),
                "seasoncode": seasoncode,
            }


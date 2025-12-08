"""
Cliente HTTP para consumir la API oficial de Euroleague.

Proporciona métodos base para obtener datos de:
- Teams (Equipos)
- Players (Jugadores)
- Games (Partidos)
- Player Stats (Estadísticas de Jugadores)
- Standings (Clasificaciones)
- Team Stats (Estadísticas de Equipos)

Este cliente maneja:
- Autenticación y headers
- Rate limiting
- Reintentos en caso de errores temporales
- Timeouts
- Logging detallado
"""

import httpx
import logging
import time
import xmltodict
from typing import Optional, Dict, Any, List
from urllib.parse import urljoin

# Configurar logging
logger = logging.getLogger(__name__)


class EuroleagueClientError(Exception):
    """Excepción base para errores del cliente de Euroleague."""

    pass


class EuroleagueAPIError(EuroleagueClientError):
    """Error en la respuesta de la API de Euroleague."""

    pass


class EuroleagueRateLimitError(EuroleagueClientError):
    """Se ha excedido el límite de tasas (rate limit) de la API."""

    pass


class EuroleagueTimeoutError(EuroleagueClientError):
    """Timeout en la solicitud a la API."""

    pass


class EuroleagueClient:
    """
    Cliente HTTP para la API oficial de Euroleague.

    Maneja:
    - Configuración de conexión HTTP
    - Autenticación y headers
    - Reintentos automáticos
    - Rate limiting
    - Logging detallado

    Ejemplo de uso:
        client = EuroleagueClient()
        teams = client.get_teams()
        players = client.get_players()
        standings = client.get_standings(season=2023)
        teamstats = client.get_teamstats(season=2023)
    """

    # URL base de la API de Euroleague
    # Documentación: https://api-live.euroleague.net/swagger/index.html
    # NOTA: La API retorna XML, no JSON
    BASE_URL = "https://api-live.euroleague.net"

    # Endpoints principales (v1)
    # Referencia: https://api-live.euroleague.net/swagger/index.html
    ENDPOINTS = {
        "teams": "/v1/teams",
        "players": "/v1/players", 
        "standings": "/v1/standings",
        "teamstats": "/v1/teamstats",
        "games": "/v1/games",
        "playerstats": "/v1/playerstats",
    }

    # Configuración de reintentos
    MAX_RETRIES = 3
    RETRY_BACKOFF_FACTOR = 0.5  # segundos
    RETRY_BACKOFF_MAX = 10  # segundos máximo de espera

    # Configuración de timeout
    REQUEST_TIMEOUT = 30  # segundos

    # Códigos HTTP considerados como errores temporales (retry)
    RETRYABLE_STATUS_CODES = {408, 429, 500, 502, 503, 504}

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: Optional[int] = None,
    ):
        """
        Inicializar el cliente de Euroleague.

        Args:
            api_key: API key de Euroleague (opcional si la API es pública).
            base_url: URL base de la API (por defecto: BASE_URL).
            timeout: Timeout para las solicitudes en segundos.
        """
        self.api_key = api_key
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout or self.REQUEST_TIMEOUT

        # Headers por defecto
        # NOTA: La API retorna XML, no JSON
        self.headers = {
            "User-Agent": "EuroleagueStatsAI/1.0",
            "Accept": "application/xml",
        }

        # Añadir autenticación si se proporciona API key
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
            logger.info("EuroleagueClient inicializado con autenticación API Key")
        else:
            logger.info("EuroleagueClient inicializado sin autenticación (API pública)")

        logger.debug(f"Base URL: {self.base_url}")
        logger.debug(f"Timeout: {self.timeout}s")

    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Realizar una solicitud HTTP con reintentos y manejo de errores.

        Args:
            method: Método HTTP (GET, POST, etc.)
            endpoint: Endpoint de la API (ej. "/v3/teams")
            params: Parámetros de query
            data: Datos para el cuerpo de la solicitud

        Returns:
            Respuesta JSON de la API

        Raises:
            EuroleagueAPIError: Error en la respuesta de la API
            EuroleagueRateLimitError: Se excedió el rate limit
            EuroleagueTimeoutError: Timeout en la solicitud
        """
        url = urljoin(self.base_url, endpoint)
        retries = 0

        while retries <= self.MAX_RETRIES:
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    logger.debug(
                        f"Solicitud {method} a {url} "
                        f"(intento {retries + 1}/{self.MAX_RETRIES + 1})"
                    )

                    response = await client.request(
                        method, url, params=params, json=data, headers=self.headers
                    )

                    # Verificar si la respuesta fue exitosa
                    if response.status_code == 200:
                        logger.debug(f"Respuesta exitosa de {url}")
                        # La API retorna XML, convertir a diccionario
                        try:
                            xml_dict = xmltodict.parse(response.text)
                            return xml_dict
                        except Exception as e:
                            logger.error(f"Error parseando XML: {e}")
                            raise EuroleagueAPIError(
                                f"Error parseando respuesta XML: {str(e)}"
                            )

                    # Manejo de errores específicos
                    if response.status_code == 429:
                        # Rate limit
                        raise EuroleagueRateLimitError(
                            f"Rate limit excedido. Status: {response.status_code}"
                        )

                    if response.status_code in self.RETRYABLE_STATUS_CODES:
                        # Error temporal, reintentar
                        retries += 1
                        if retries > self.MAX_RETRIES:
                            raise EuroleagueAPIError(
                                f"Error {response.status_code} después de "
                                f"{self.MAX_RETRIES} reintentos. Respuesta: {response.text}"
                            )

                        wait_time = (
                            self.RETRY_BACKOFF_FACTOR * (2 ** (retries - 1))
                        )
                        wait_time = min(wait_time, self.RETRY_BACKOFF_MAX)
                        logger.warning(
                            f"Error temporal {response.status_code}. "
                            f"Reintentando en {wait_time:.2f}s..."
                        )
                        time.sleep(wait_time)
                        continue

                    # Otros errores HTTP
                    raise EuroleagueAPIError(
                        f"Error HTTP {response.status_code} en {url}. "
                        f"Respuesta: {response.text}"
                    )

            except httpx.TimeoutException as e:
                logger.error(f"Timeout en solicitud a {url}: {str(e)}")
                retries += 1
                if retries > self.MAX_RETRIES:
                    raise EuroleagueTimeoutError(
                        f"Timeout después de {self.MAX_RETRIES} reintentos"
                    ) from e

                wait_time = (
                    self.RETRY_BACKOFF_FACTOR * (2 ** (retries - 1))
                )
                wait_time = min(wait_time, self.RETRY_BACKOFF_MAX)
                logger.warning(
                    f"Timeout. Reintentando en {wait_time:.2f}s..."
                )
                time.sleep(wait_time)
                continue

            except httpx.RequestError as e:
                logger.error(f"Error de solicitud a {url}: {str(e)}")
                retries += 1
                if retries > self.MAX_RETRIES:
                    raise EuroleagueClientError(
                        f"Error de solicitud después de {self.MAX_RETRIES} reintentos: {str(e)}"
                    ) from e

                wait_time = (
                    self.RETRY_BACKOFF_FACTOR * (2 ** (retries - 1))
                )
                wait_time = min(wait_time, self.RETRY_BACKOFF_MAX)
                logger.warning(
                    f"Error de solicitud. Reintentando en {wait_time:.2f}s..."
                )
                time.sleep(wait_time)
                continue

        raise EuroleagueClientError(
            f"Fallo máximo de reintentos alcanzado para {url}"
        )

    async def get_teams(self) -> Dict[str, Any]:
        """
        Obtener lista de equipos.

        Returns:
            Datos de equipos en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info("Obteniendo lista de equipos...")
        return await self._make_request("GET", self.ENDPOINTS["teams"])

    async def get_players(self, season: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener lista de jugadores.

        Args:
            season: Temporada opcional para filtrar

        Returns:
            Datos de jugadores en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info(f"Obteniendo lista de jugadores (temporada: {season})...")
        params = {}
        if season:
            params["SeasonCode"] = f"E{season}"

        return await self._make_request("GET", self.ENDPOINTS["players"], params=params)

    async def get_standings(self, season: Optional[int] = None) -> Dict[str, Any]:
        """
        Obtener clasificaciones.

        Args:
            season: Temporada opcional para filtrar

        Returns:
            Datos de clasificaciones en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info(f"Obteniendo clasificaciones (temporada: {season})...")
        params = {}
        if season:
            params["SeasonCode"] = f"E{season}"

        return await self._make_request(
            "GET", self.ENDPOINTS["standings"], params=params
        )

    async def get_teamstats(
        self, season: Optional[int] = None, round_: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de equipos.

        Args:
            season: Temporada opcional para filtrar
            round_: Jornada opcional para filtrar

        Returns:
            Datos de estadísticas de equipos en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info(
            f"Obteniendo estadísticas de equipos "
            f"(temporada: {season}, jornada: {round_})..."
        )
        params = {}
        if season:
            params["SeasonCode"] = f"E{season}"
        if round_:
            params["Round"] = round_

        return await self._make_request(
            "GET", self.ENDPOINTS["teamstats"], params=params
        )

    async def get_games(
        self, season: Optional[int] = None, round_: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtener datos de partidos (games).

        Args:
            season: Temporada opcional para filtrar
            round_: Jornada opcional para filtrar

        Returns:
            Datos de partidos en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info(
            f"Obteniendo partidos (temporada: {season}, jornada: {round_})..."
        )
        params = {}
        if season:
            params["SeasonCode"] = f"E{season}"
        if round_:
            params["Round"] = round_

        return await self._make_request(
            "GET", self.ENDPOINTS["games"], params=params
        )

    async def get_playerstats(
        self,
        seasoncode: Optional[str] = None,
        playercode: Optional[str] = None,
        round_: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Obtener estadísticas de jugadores (box scores).

        Args:
            seasoncode: Código de temporada (ej: "E2025", "E2024")
            playercode: Código del jugador (ej: "DECK", "PAU", "LLULL")
            round_: Jornada opcional para filtrar

        Returns:
            Datos de estadísticas de jugadores en formato JSON

        Raises:
            EuroleagueClientError: Error en la solicitud
        """
        logger.info(
            f"Obteniendo estadísticas de jugadores "
            f"(temporada: {seasoncode}, jugador: {playercode}, jornada: {round_})..."
        )
        params = {}
        if seasoncode:
            params["SeasonCode"] = seasoncode
        if playercode:
            params["PlayerCode"] = playercode
        if round_:
            params["Round"] = round_

        return await self._make_request(
            "GET", self.ENDPOINTS["playerstats"], params=params
        )

    def get_endpoint_url(self, endpoint_name: str) -> str:
        """
        Obtener la URL completa de un endpoint.

        Args:
            endpoint_name: Nombre del endpoint (ej. 'teams', 'players')

        Returns:
            URL completa del endpoint
        """
        if endpoint_name not in self.ENDPOINTS:
            raise EuroleagueClientError(
                f"Endpoint desconocido: {endpoint_name}. "
                f"Endpoints disponibles: {list(self.ENDPOINTS.keys())}"
            )

        return urljoin(self.base_url, self.ENDPOINTS[endpoint_name])


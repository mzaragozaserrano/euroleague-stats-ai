Feature: Cliente Base de Euroleague API

  Como desarrollador ETL,
  Quiero tener un cliente HTTP robusto,
  Para consumir datos de la API de Euroleague de forma confiable.

  Scenario: Cliente puede conectarse a la API de Euroleague
    Given el cliente de Euroleague está inicializado
    When se realiza una solicitud GET a /v3/teams
    Then la respuesta debe tener estado 200
    And la respuesta debe contener datos de equipos

  Scenario: Cliente maneja errores temporales con reintentos
    Given el cliente de Euroleague está inicializado
    When la API devuelve un error 503
    Then el cliente debe reintentar la solicitud
    And el cliente debe hacer máximo 3 reintentos

  Scenario: Cliente genera un error después de múltiples fallos
    Given el cliente de Euroleague está inicializado
    When la API falla en todos los reintentos
    Then debe generarse una excepción EuroleagueAPIError

  Scenario: Cliente maneja rate limiting correctamente
    Given el cliente de Euroleague está inicializado
    When la API devuelve un error 429 (rate limit)
    Then debe generarse una excepción EuroleagueRateLimitError

  Scenario: Métodos específicos del cliente funcionan correctamente
    Given el cliente de Euroleague está inicializado
    When se llama a get_teams()
    Then debe devolver datos de equipos
    When se llama a get_players()
    Then debe devolver datos de jugadores
    When se llama a get_games()
    Then debe devolver datos de partidos


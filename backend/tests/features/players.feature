Feature: Ingesta de Jugadores desde la API de Euroleague

  Como ingeniero de datos ETL,
  Quiero procesar datos de jugadores desde la API de Euroleague,
  Para cargar automáticamente los jugadores en la base de datos
  Y mantener la información de plantillas actualizada.

  Scenario: API devuelve datos válidos de jugadores
    Given la API de Euroleague está disponible
    And la API retorna datos válidos de jugadores
    When se ejecuta el ETL de jugadores
    Then la solicitud GET a /v3/players debe tener estado 200
    And la respuesta debe contener una lista de jugadores con campos: id, name, first_name, last_name, jersey_number, team_id

  Scenario: Nuevos jugadores se insertan en la base de datos
    Given la API de Euroleague está disponible
    And la API retorna 5 jugadores nuevos
    And la base de datos tiene equipos previos cargados
    And la base de datos no contiene jugadores
    When se ejecuta el ETL de jugadores
    Then la base de datos debe contener exactamente 5 jugadores
    And cada jugador debe tener los campos requeridos: id, name, team_id
    And cada jugador debe estar asociado a un equipo válido

  Scenario: Jugadores existentes se actualizan correctamente
    Given la API de Euroleague está disponible
    And la base de datos contiene 1 jugador con id=1, name="Juan Carlos Navarro", team_id=1
    And la API retorna el jugador con id=1, name="Juan Carlos Navarro Valverde", team_id=1 (información actualizada)
    When se ejecuta el ETL de jugadores
    Then la base de datos debe contener exactamente 1 jugador
    And el nombre del jugador con id=1 debe ser actualizado a "Juan Carlos Navarro Valverde"

  Scenario: Se evita duplicación de jugadores
    Given la API de Euroleague está disponible
    And la API retorna 10 jugadores
    And la base de datos ya contiene 7 de esos jugadores
    When se ejecuta el ETL de jugadores
    Then la base de datos debe contener exactamente 10 jugadores
    And no deben haber duplicados

  Scenario: Los jugadores se asocian correctamente a sus equipos
    Given la API de Euroleague está disponible
    And la base de datos contiene 2 equipos con id=1, id=2
    And la API retorna 3 jugadores del equipo id=1 y 2 jugadores del equipo id=2
    When se ejecuta el ETL de jugadores
    Then la base de datos debe contener exactamente 5 jugadores
    And 3 jugadores deben estar asociados al equipo id=1
    And 2 jugadores deben estar asociados al equipo id=2

  Scenario: El ETL maneja errores de API correctamente
    Given la API de Euroleague está disponible
    And la API devuelve un error 503
    When se ejecuta el ETL de jugadores
    Then debe capturarse la excepción EuroleagueAPIError
    And la base de datos debe permanecer sin cambios

  Scenario: El ETL valida campos obligatorios
    Given la API de Euroleague está disponible
    And la API retorna datos de jugadores con campos faltantes (falta name o team_id)
    When se ejecuta el ETL de jugadores
    Then el ETL debe validar los campos requeridos
    And los jugadores con campos obligatorios incompletos deben ser rechazados

  Scenario: El ETL maneja relaciones de clave foránea
    Given la API de Euroleague está disponible
    And la base de datos está vacía (sin equipos)
    And la API retorna jugadores que referencian equipos inexistentes
    When se ejecuta el ETL de jugadores
    Then el ETL debe validar que team_id exista en la tabla de equipos
    And los jugadores con team_id inválidos deben ser rechazados

  Scenario: Múltiples ejecuciones del ETL son idempotentes
    Given la API de Euroleague está disponible
    And la API retorna 5 jugadores
    And la base de datos no contiene jugadores
    When se ejecuta el ETL de jugadores
    Then la base de datos debe contener exactamente 5 jugadores
    When se ejecuta el ETL de jugadores nuevamente
    Then la base de datos debe contener exactamente 5 jugadores
    And no deben haber duplicados después de múltiples ejecuciones



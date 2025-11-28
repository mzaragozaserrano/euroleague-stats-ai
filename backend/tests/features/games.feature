Feature: Ingesta de Partidos y Estadísticas de Jugadores desde la API de Euroleague

  Como ingeniero de datos ETL,
  Quiero procesar datos de partidos y estadísticas de jugadores desde la API de Euroleague,
  Para cargar automáticamente los partidos y box scores en la base de datos
  Y mantener las estadísticas granulares de los jugadores actualizadas.

  Scenario: API devuelve datos válidos de partidos
    Given la API de Euroleague está disponible
    And la API retorna datos válidos de partidos
    When se ejecuta el ETL de partidos
    Then la solicitud GET a /v3/games debe tener estado 200
    And la respuesta debe contener una lista de partidos con campos: id, season, round, home_team_id, away_team_id, date, home_score, away_score

  Scenario: Nuevos partidos se insertan en la base de datos
    Given la API de Euroleague está disponible
    And la API retorna 3 partidos nuevos
    And la base de datos tiene equipos previos cargados
    And la base de datos no contiene partidos
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 3 partidos
    And cada partido debe tener los campos requeridos: id, season, round, home_team_id, away_team_id, date

  Scenario: Partidos jugados vs programados se diferencian correctamente
    Given la API de Euroleague está disponible
    And la API retorna 2 partidos jugados con puntuaciones finales y 1 partido programado sin puntuaciones
    And la base de datos tiene equipos previos cargados
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 3 partidos
    And 2 partidos deben tener home_score y away_score completados
    And 1 partido debe tener home_score y away_score como NULL (programado)

  Scenario: Partidos existentes se actualizan correctamente
    Given la API de Euroleague está disponible
    And la base de datos contiene 1 partido con id=1, home_score=80, away_score=75 (partido inicial)
    And la API retorna el partido con id=1, home_score=85, away_score=80 (puntuaciones actualizadas)
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 1 partido
    And las puntuaciones del partido con id=1 deben ser actualizadas a home_score=85, away_score=80

  Scenario: Estadísticas anidadas de jugadores se insertan correctamente
    Given la API de Euroleague está disponible
    And la base de datos tiene equipos, jugadores y partidos previos cargados
    And la API retorna estadísticas de jugadores (box scores) para los partidos
    When se ejecuta el ETL de estadísticas de partidos
    Then la base de datos debe contener estadísticas de player_stats_games
    And cada estadística debe tener los campos requeridos: game_id, player_id, team_id, minutes, points, rebounds_total, assists

  Scenario: Se evita duplicación de partidos
    Given la API de Euroleague está disponible
    And la API retorna 4 partidos
    And la base de datos ya contiene 2 de esos partidos
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 4 partidos
    And no deben haber duplicados de partidos

  Scenario: Los partidos se asocian correctamente a los equipos
    Given la API de Euroleague está disponible
    And la base de datos contiene 3 equipos con id=1, id=2, id=3
    And la API retorna 3 partidos: (1 vs 2), (2 vs 3), (1 vs 3)
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 3 partidos
    And cada partido debe tener home_team_id y away_team_id que existan en la tabla de equipos

  Scenario: Estadísticas anidadas se asocian correctamente a partidos y jugadores
    Given la API de Euroleague está disponible
    And la base de datos tiene 2 partidos, 10 jugadores y 2 equipos cargados
    And la API retorna box scores para los partidos con 5 jugadores por equipo por partido
    When se ejecuta el ETL de estadísticas de partidos
    Then la base de datos debe contener 20 registros de player_stats_games (5 jugadores x 2 equipos x 2 partidos)
    And cada estadística debe estar asociada a un game_id, player_id y team_id válidos

  Scenario: El ETL maneja errores de API correctamente para partidos
    Given la API de Euroleague está disponible
    And la API devuelve un error 503 para la solicitud de partidos
    When se ejecuta el ETL de partidos
    Then debe capturarse la excepción EuroleagueAPIError
    And la base de datos debe permanecer sin cambios

  Scenario: El ETL valida campos obligatorios de partidos
    Given la API de Euroleague está disponible
    And la API retorna datos de partidos con campos faltantes (falta home_team_id o away_team_id)
    When se ejecuta el ETL de partidos
    Then el ETL debe validar los campos requeridos de partidos
    And los partidos con campos obligatorios incompletos deben ser rechazados

  Scenario: El ETL maneja relaciones de clave foránea para partidos
    Given la API de Euroleague está disponible
    And la base de datos está vacía (sin equipos)
    And la API retorna partidos que referencian equipos inexistentes
    When se ejecuta el ETL de partidos
    Then el ETL debe validar que home_team_id y away_team_id existan en la tabla de equipos
    And los partidos con team_id inválidos deben ser rechazados

  Scenario: Estadísticas de jugadores validan relaciones de clave foránea
    Given la API de Euroleague está disponible
    And la base de datos tiene equipos y partidos cargados
    And la API retorna estadísticas de jugadores con player_id que no existen en la BD
    When se ejecuta el ETL de estadísticas de partidos
    Then el ETL debe validar que player_id exista en la tabla de players
    And las estadísticas con player_id inválidos deben ser rechazadas

  Scenario: Múltiples ejecuciones del ETL de partidos son idempotentes
    Given la API de Euroleague está disponible
    And la API retorna 2 partidos
    And la base de datos tiene equipos previos cargados
    And la base de datos no contiene partidos
    When se ejecuta el ETL de partidos
    Then la base de datos debe contener exactamente 2 partidos
    When se ejecuta el ETL de partidos nuevamente
    Then la base de datos debe contener exactamente 2 partidos
    And no deben haber duplicados de partidos después de múltiples ejecuciones

  Scenario: Estadísticas de jugadores se actualizan sin duplicar registros
    Given la API de Euroleague está disponible
    And la base de datos tiene 1 partido, 2 jugadores y 1 equipo cargados
    And la base de datos contiene 2 registros de player_stats_games para ese partido
    And la API retorna box scores actualizados para los mismos 2 jugadores
    When se ejecuta el ETL de estadísticas de partidos
    Then la base de datos debe contener exactamente 2 registros de player_stats_games para ese partido
    And los puntos de los jugadores deben ser actualizados a los nuevos valores

  Scenario: El PIR se calcula correctamente en estadísticas de jugadores
    Given la API de Euroleague está disponible
    And la base de datos tiene 1 partido, 1 jugador y 1 equipo cargados
    And la API retorna estadísticas de jugador con puntos=20, rebotes=8, asistencias=5, faltas_cometidas=2
    When se ejecuta el ETL de estadísticas de partidos
    Then la base de datos debe contener 1 registro de player_stats_games
    And el PIR debe calcularse correctamente basándose en las estadísticas



Feature: Ingesta de Equipos desde la API de Euroleague

  Como ingeniero de datos ETL,
  Quiero procesar datos de equipos desde la API de Euroleague,
  Para cargar automáticamente los equipos en la base de datos
  Y mantener la información actualizada.

  Scenario: API devuelve datos válidos de equipos
    Given la API de Euroleague está disponible
    And la API retorna datos válidos de equipos
    When se ejecuta el ETL de equipos
    Then la solicitud GET a /v3/teams debe tener estado 200
    And la respuesta debe contener una lista de equipos con campos: id, name, code, logo_url

  Scenario: Nuevos equipos se insertan en la base de datos
    Given la API de Euroleague está disponible
    And la API retorna 2 equipos nuevos
    And la base de datos está vacía
    When se ejecuta el ETL de equipos
    Then la base de datos debe contener exactamente 2 equipos
    And cada equipo debe tener los campos requeridos: id, name, code, logo_url

  Scenario: Equipos existentes se actualizan correctamente
    Given la API de Euroleague está disponible
    And la base de datos contiene 1 equipo con id=1, name="Real Madrid", code="RMB"
    And la API retorna el equipo con id=1, name="Real Madrid CF", code="RMB" (información actualizada)
    When se ejecuta el ETL de equipos
    Then la base de datos debe contener exactamente 1 equipo
    And el nombre del equipo con id=1 debe ser actualizado a "Real Madrid CF"

  Scenario: Se evita duplicación de equipos
    Given la API de Euroleague está disponible
    And la API retorna 3 equipos
    And la base de datos ya contiene 2 de esos equipos
    When se ejecuta el ETL de equipos
    Then la base de datos debe contener exactamente 3 equipos
    And no deben haber duplicados

  Scenario: El ETL maneja errores de API correctamente
    Given la API de Euroleague está disponible
    And la API devuelve un error 503
    When se ejecuta el ETL de equipos
    Then debe capturarse la excepción EuroleagueAPIError
    And la base de datos debe permanecer sin cambios

  Scenario: El ETL valida campos obligatorios
    Given la API de Euroleague está disponible
    And la API retorna datos con campos faltantes (falta logo_url)
    When se ejecuta el ETL de equipos
    Then el ETL debe validar los campos requeridos
    And los equipos con campos incompletos deben ser rechazados o completados con valores por defecto

  Scenario: Múltiples ejecuciones del ETL son idempotentes
    Given la API de Euroleague está disponible
    And la API retorna 2 equipos
    And la base de datos está vacía
    When se ejecuta el ETL de equipos
    Then la base de datos debe contener exactamente 2 equipos
    When se ejecuta el ETL de equipos nuevamente
    Then la base de datos debe contener exactamente 2 equipos
    And no deben haber duplicados después de múltiples ejecuciones


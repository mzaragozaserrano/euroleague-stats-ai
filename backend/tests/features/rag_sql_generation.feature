Feature: RAG SQL Generation - Validación de Precisión SQL

  Como desarrollador de IA,
  Quiero validar que el motor de generación SQL produce queries correctas, seguras y eficientes,
  Para garantizar que las respuestas del chatbot son precisas y confiables.

  Background:
    Given la base de datos contiene equipos, jugadores y estadísticas precargadas
    And el servicio de vectorización está disponible
    And el LLM (OpenRouter) está disponible
    And la tabla schema_embeddings contiene metadatos de tablas y columnas

  Scenario: SQL generado incluye ORDER BY para queries de ranking
    Given una consulta que solicita "mejores equipos por puntos"
    When genero SQL mediante LLM
    Then el SQL contiene la cláusula ORDER BY DESC
    And el SQL es sintácticamente válido en PostgreSQL
    And la ejecución retorna resultados ordenados descendentemente

  Scenario: SQL generado incluye LIMIT/TOP para queries acotadas
    Given una consulta que solicita "top 5 jugadores con más puntos"
    When genero SQL mediante LLM
    Then el SQL contiene LIMIT 5 o TOP 5
    And el resultado tiene máximo 5 filas
    And el SQL es ejecutable sin errores

  Scenario: SQL rechaza inyecciones maliciosas - DROP TABLE
    Given una consulta maliciosa que intenta "DROP TABLE players"
    When intento generar SQL
    Then el servicio rechaza la consulta
    And retorna error con mensaje "Consulta peligrosa detectada"
    And no se ejecuta ningún SQL contra la BD

  Scenario: SQL rechaza inyecciones maliciosas - DELETE masivo
    Given una consulta maliciosa que intenta "DELETE FROM games WHERE 1=1"
    When intento generar SQL
    Then el servicio rechaza la consulta
    And retorna error con mensaje "Consulta peligrosa detectada"
    And la integridad de los datos se mantiene

  Scenario: RAG retrieval recupera schema relevante desde historial
    Given un historial de chat con 3 mensajes previos sobre "estadísticas de jugadores"
    And una nueva consulta "puntos de Larkin"
    When ejecuto RAG retrieval con contexto de historial
    Then se retornan metadatos de tabla player_stats_games
    And se retornan metadatos de columna points
    And el similarity score está en rango [0.5, 1.0]

  Scenario: RAG retrieval sin historial todavía recupera schema correcto
    Given sin historial previo (primera consulta)
    And una consulta "jugadores del Real Madrid"
    When ejecuto RAG retrieval
    Then se retornan metadatos de tabla players
    And se retornan metadatos de tabla teams
    And el contexto recuperado es relevante para la consulta

  Scenario: SQL generado usa aliases correctos para joined tables
    Given una consulta sobre "estadísticas de jugador con nombre de equipo"
    When genero SQL
    Then el SQL contiene JOINs con aliases (p, t, g, ps)
    And los aliases son consistentes en toda la query
    And la ejecución no produce error de ambigüedad de columnas

  Scenario: Query sin resultados retorna data vacía sin error
    Given una consulta válida pero con filtros que no coinciden "jugador fantasma"
    When genero y ejecuto SQL
    Then data es un array vacío []
    And no hay campo error en la respuesta
    And visualization es 'table'

  Scenario: SQL maneja NULL values correctamente
    Given una consulta que podría retornar valores NULL "assists por jugador"
    When genero SQL
    Then el SQL maneja explícitamente NULLs (COALESCE o IS NULL)
    And la ejecución retorna valores sin errores
    And los NULLs se representan como null en JSON

  Scenario: Timeout en LLM reintenta con exponential backoff
    Given el LLM responde lentamente (> 10 segundos)
    When intento generar SQL con timeout de 5 segundos
    Then el servicio reintenta automáticamente
    And después de 3 reintentos falla gracefully
    And retorna error con mensaje "LLM no disponible después de reintentos"

  Scenario: Embedding no encontrado en schema_embeddings falla gracefully
    Given una consulta válida pero la tabla schema_embeddings está vacía
    When intento ejecutar RAG retrieval
    Then el servicio detecta que no hay embeddings
    And retorna error con mensaje "No se pudo recuperar metadatos de schema"
    And el backend no crashea

  Scenario: SQL generado ejecuta en menos de 3 segundos
    Given una consulta válida sobre datos agregados
    When genero y ejecuto SQL
    Then el tiempo de ejecución es < 3 segundos
    And se reporta latencia en la respuesta
    And la latencia es confiable para UI

  Scenario: Validación SQL previene UPDATE/DELETE en queries de usuario
    Given una consulta que intenta "UPDATE players SET name = 'hack'"
    When genero SQL
    Then el SQL se valida y se rechaza
    And error explica "No se permiten operaciones de modificación"

  Scenario: Agregaciones en SQL son sintácticamente correctas
    Given una consulta sobre "promedio de puntos por equipo"
    When genero SQL
    Then el SQL contiene GROUP BY equipo
    And el SQL contiene agregación (SUM, AVG, COUNT, etc.)
    And la ejecución retorna resultados agrupados correctamente

  Scenario: SQL maneja strings con caracteres especiales correctamente
    Given una consulta sobre "jugador con nombre Miličević"
    When genero SQL
    Then el SQL escapa caracteres especiales correctamente
    And el encoding UTF-8 se mantiene
    And la búsqueda retorna resultados exactos o similares

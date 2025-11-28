Feature: Chat Endpoint - Orquestacion del Pipeline de IA

  Como usuario del frontend,
  Quiero enviar una consulta natural al endpoint /api/chat,
  Para obtener datos SQL-generados, visualización recomendada y manejo de errores robusto.

  Background:
    Given la base de datos contiene equipos, jugadores y estadisticas precargadas
    And el servicio de vectorizacion esta disponible
    And el LLM (OpenRouter) esta disponible

  Scenario: Chat endpoint retorna respuesta valida para consulta simple
    Given una consulta valida "puntos de Larkin en la temporada"
    When se envía una solicitud POST a /api/chat con query y history vacío
    Then la respuesta tiene status 200
    And la respuesta contiene un campo sql con una consulta valida
    And la respuesta contiene un campo data con resultados
    And la respuesta contiene un campo visualization con tipo 'table'
    And la respuesta no tiene campo error

  Scenario: Chat endpoint maneja historia de conversacion
    Given una consulta valida "puntos de Larkin"
    And una historia de conversacion previa con 2 mensajes
    When se envía una solicitud POST a /api/chat con query e history
    Then la respuesta tiene status 200
    And el LLM recibe el contexto de historia en el prompt
    And la respuesta contiene sql, data y visualization

  Scenario: Chat endpoint detecta visualizacion apropiada
    Given una consulta que solicita comparacion de datos "puntos por equipo"
    When se envía una solicitud POST a /api/chat
    Then la respuesta contiene visualization = 'bar' o 'line'
    And los datos son multiples puntos para un grafico

  Scenario: Chat endpoint valida consultas SQL peligrosas
    Given una consulta maliciosa que intenta "DROP TABLE players"
    When se envía una solicitud POST a /api/chat
    Then la respuesta tiene status 200
    And la respuesta contiene un campo error explicando "Consulta peligrosa rechazada"
    And no se ejecuta ningun SQL

  Scenario: Chat endpoint maneja errores de BD sin crashear
    Given la base de datos esta temporalmente desconectada
    When se envía una solicitud POST a /api/chat con una consulta valida
    Then la respuesta tiene status 200
    And la respuesta contiene un campo error explicando "No se pudo conectar a la BD"
    And el backend no crashea

  Scenario: Chat endpoint maneja errores del LLM sin crashear
    Given el LLM (OpenRouter) esta temporalmente inaccesible
    When se envía una solicitud POST a /api/chat
    Then la respuesta tiene status 200
    And la respuesta contiene un campo error explicando "LLM no disponible"
    And el backend no crashea

  Scenario: Chat endpoint retorna logs de RAG retrieval en stdout
    Given una consulta "estadisticas de Micic"
    When se envía una solicitud POST a /api/chat
    Then los logs muestran "RAG retrieval: <N> documentos encontrados"
    And los logs muestran el similarity score de cada documento

  Scenario: Chat endpoint responde en menos de 5 segundos
    Given una consulta valida
    When se envía una solicitud POST a /api/chat
    Then la respuesta se recibe en menos de 5 segundos
    And el tiempo de latencia se reporta en la respuesta

  Scenario: Chat endpoint maneja queries sin resultados
    Given una consulta valida pero sin coincidencias en BD "jugador inexistente X"
    When se envía una solicitud POST a /api/chat
    Then la respuesta tiene status 200
    And la respuesta contiene data = [] (lista vacia)
    And la respuesta contiene visualization = 'table'
    And no hay campo error (es una respuesta valida)

  Scenario: Chat endpoint valida request schema
    Given un request sin campo query
    When se envía una solicitud POST a /api/chat sin query
    Then la respuesta tiene status 422 (Unprocessable Entity)
    And la respuesta contiene detalles del error de validacion

  Scenario: RAG retrieval utiliza vector similarity correctamente
    Given una consulta "puntos del jugador"
    When se ejecuta RAG retrieval para encontrar esquema relevante
    Then se retornan metadatos sobre tabla player_stats_games
    And se retornan metadatos sobre columna points
    And los resultados ordenados por similarity descendente

  Scenario: SQL generado es ejecutable contra la BD
    Given una consulta valida "promedio de puntos por equipo"
    When se genera SQL mediante LLM
    Then el SQL cumple con restricciones de seguridad (no DROP/DELETE)
    And el SQL es valido PostgreSQL
    And el SQL se ejecuta exitosamente contra Neon
    And se retornan resultados en formato JSON



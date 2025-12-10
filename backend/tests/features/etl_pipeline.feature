Feature: ETL Pipeline de Euroleague
  Como administrador del sistema
  Quiero que el ETL obtenga datos de la API de Euroleague
  Para mantener la BD actualizada con equipos, jugadores y estadísticas

  Background:
    Given La base de datos está limpia
    And Las conexiones a APIs están disponibles

  Scenario: Ingesta de equipos funciona correctamente
    When Ejecuto el script de ingesta de equipos
    Then Se insertan equipos en la tabla teams
    And La tabla teams contiene al menos 18 equipos
    And Cada equipo tiene un código único (code)

  Scenario: Ingesta de jugadores funciona correctamente
    Given Los equipos ya están en la BD
    When Ejecuto el script de ingesta de jugadores para temporada 2025
    Then Se insertan jugadores en la tabla players
    And Cada jugador está asociado a un equipo válido
    And Cada jugador tiene un player_code único
    And Los jugadores tienen posiciones válidas (Base, Escolta, Alero, Ala-Pivot, Pivot)

  Scenario: Ingesta de estadísticas por temporada funciona
    Given Los equipos y jugadores ya están en la BD
    When Ejecuto el script de ingesta de estadísticas para temporada 2025
    Then Se insertan estadísticas en player_season_stats
    And Cada estadística está asociada a un jugador válido
    And Las estadísticas contienen campos: points, rebounds, assists, pir

  Scenario: ETL Pipeline completo en orden correcto
    When Ejecuto el script run_etl.py
    Then Se ejecutan los scripts en orden: teams → players → stats
    And No hay errores en el proceso
    And La BD contiene datos válidos en las 3 tablas

  Scenario: Normalización Unicode en búsquedas
    Given Los jugadores "Llull" y "Llúll" están en la BD
    When Busco por el jugador "llull" sin tildes
    Then El sistema encuentra al jugador independientemente de las tildes
    And El resultado retorna el nombre correcto con tilde (como dicta la API)

  Scenario: Consultas de estadísticas detectan correctamente
    Given La BD tiene datos de jugadores y estadísticas
    When El usuario pregunta "máximos anotadores"
    Then El servicio text_to_sql detecta como query de stats
    And Retorna datos desde player_season_stats sin usar LLM

  Scenario: Consultas de partidos se rechazan adecuadamente
    When El usuario pregunta "partidos de Larkin con más de 10 puntos"
    Then El servicio text_to_sql detecta como query de partidos
    And Retorna error informativo: "datos detallados por partido"
    And NO intenta generar SQL

  Scenario: Caché de temporadas pasadas funciona
    Given El usuario pregunta por temporada 2024
    When No hay datos de 2024 en la BD
    Then El frontend cachea en localStorage
    And Las consultas futuras de 2024 usan la caché local
    And No se intenta refrescar con ETL automático

  Scenario: Equipo en consulta se detecta correctamente
    Given La BD tiene datos
    When El usuario pregunta "máximos anotadores del Real Madrid"
    Then El sistema detecta "Real Madrid" → código "RM"
    And Filtra resultados por team_code = "RM"




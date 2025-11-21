# Archivo: euroleague_stats.feature

Feature: Motor de Consulta de Estadísticas de la Euroliga mediante Lenguaje Natural

  Como aficionado avanzado o analista,
  Quiero hacer preguntas complejas en lenguaje natural
  Para obtener datos visualizados de forma instantánea
  Y reducir la fricción en la investigación de estadísticas.

  ---
  
  ## Escenario 1: Consulta Rápida de Comparativa de Jugadores (MVP - Nivel Gratuito)
  
  Scenario: Comparación Directa de Dos Jugadores
    Given el usuario está en la interfaz principal de consulta
    And la base de datos de Estadísticas Básicas está completamente cargada y accesible
    When el usuario ingresa la consulta: "Comparativa de % de tiros libres entre Sloukas y James esta temporada" y presiona Enter
    Then el sistema debe mostrar el resultado en menos de 10 segundos
    And el sistema debe interpretar la consulta en SQL sin intervención humana
    And el resultado debe ser presentado como una **Tabla comparativa** o un **Gráfico de Barras** (visualization: 'table' o 'bar')
    But el sistema no debe requerir que el usuario navegue a través de filtros o menús.

  ---

  ## Escenario 2: El Descubrimiento Profundo y Espacial (Post-MVP - Nivel Pro)

  Scenario: Consulta Compositiva y Espacial (Text-to-Spatial-SQL)
    Given el usuario tiene una suscripción "Pro" activa
    And la base de datos incluye datos espaciales (shot-charts) y la extensión PostGIS está habilitada
    When el usuario ingresa la consulta: "Dame los 5 jugadores con el peor porcentaje defensivo en triples desde la esquina" y presiona Enter
    Then el sistema debe ejecutar la consulta Text-to-Spatial-SQL
    And el sistema debe devolver una lista de los 5 jugadores clasificados
    And el resultado debe ser presentado con una visualización relevante, como un **Shot Chart** resaltando la zona "esquina" (visualization: 'shot_chart')
    And el usuario puede refinar la consulta a continuación (ej. "Fíltralo solo para bases").

  ---

  ## Escenario 3: Transparencia y Fallo Controlado (Anti-Hallucination)

  Scenario: Manejo de Entidades Desconocidas o Ambigüedades
    Given el LLM recibe una consulta que contiene un término no mapeado al esquema de la base de datos
    When el usuario pregunta: "¿Cuántos puntos metió el alero del Barcelona en la Final Four de 1999?"
    Then el sistema debe detectar la ambigüedad o la falta de datos históricos disponibles (pre-MVP)
    And el sistema no debe generar código SQL ni alucinar una respuesta
    And el sistema debe responder con un mensaje que solicite aclaración o que indique que los datos están fuera del alcance actual.
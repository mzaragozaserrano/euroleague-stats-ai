# ESPECIFICACIÓN DEL PRODUCTO: Agente de Estadísticas IA de la Euroliga

## 1. Descripción y Visión de Alto Nivel
Estamos construyendo una **interfaz de inteligencia de datos para la Euroliga basada en lenguaje natural**.

Actualmente, el ecosistema de datos de la Euroliga está fragmentado y es manual. Los usuarios deben navegar por múltiples menús, aplicar filtros y realizar cálculos mentales para obtener respuestas. Nuestra visión es una **inversión del flujo de trabajo (workflow inversion)**: en lugar de que el usuario busque los datos, el usuario hace una pregunta y la IA recupera la respuesta.

El objetivo es crear el "Statmuse de la Euroliga": una herramienta donde la barrera entre la curiosidad del aficionado y la respuesta estadística sea cero.

## 2. El Problema Central
Los aficionados sofisticados (Fantasy, Apostadores, Analistas) sufren una fricción significativa:
* **Inaccesibilidad:** Consultas complejas (ej. "¿Quién anota más desde la esquina?") son imposibles en las herramientas actuales.
* **Lentitud:** Las comparaciones simples (ej. "Micic vs Larkin") requieren múltiples pestañas y navegación manual.
* **Desconexión:** Existe una brecha entre el vocabulario del aficionado y la estructura rígida de las bases de datos.

## 3. Público Objetivo y Personas

### A. El Jugador de Fantasy (The Fantasy Manager)
* **Necesidad:** Toma decisiones semanales sobre alineaciones. Necesita datos de tendencias recientes ("¿Quién está en racha los últimos 3 partidos?") más que promedios de temporada.
* **Punto de Dolor:** Perder tiempo revisando *box scores* individuales para detectar tendencias.

### B. El Apostador Deportivo (The Bettor)
* **Necesidad:** Busca ventajas ("edge") en mercados específicos (rebotes, asistencias, *matchups* directos). Valora la profundidad y los datos situacionales.
* **Punto de Dolor:** Falta de herramientas que crucen datos de jugadores contra oponentes específicos ("Cómo rinde Tavares contra equipos rápidos").

### C. El Aficionado "Hardcore" (The Die-Hard Fan)
* **Necesidad:** Validar argumentos en discusiones (Reddit/Twitter) y satisfacer la curiosidad pura.
* **Punto de Dolor:** Sabe que los datos existen, pero no puede acceder a ellos sin saber SQL o programar.

## 4. Viajes del Usuario y Experiencias (User Journeys)

### Journey 1: La Consulta Rápida (The Quick Fact-Check) - MVP
* **Trigger:** Un usuario está viendo un partido y surge un debate sobre quién es mejor tirador de libres **en la temporada actual**.
* **Acción:** Entra en la web (móvil) y escribe: *"Comparativa de % de tiros libres entre Sloukas y James esta temporada"*.
* **Resultado Esperado:**
    * No hay navegación por menús.
    * El sistema devuelve una **tabla comparativa** directa y un pequeño gráfico de barras.
    * Tiempo total: < 10 segundos.
    * **Nota:** Los datos mostrados son estadísticas acumuladas hasta el último partido completado (actualizadas diariamente), no incluyen estadísticas del partido en curso.

### Journey 2: El Descubrimiento Profundo (The Deep Dive) - Post-MVP
* **Trigger:** Un analista quiere escribir un hilo sobre la defensa de perímetro.
* **Acción:** Escribe: *"Dame los 5 jugadores con el peor porcentaje defensivo en triples desde la esquina"*.
* **Resultado Esperado:**
    * El sistema interpreta "esquina" como una consulta espacial (Spatial SQL).
    * Genera una lista ordenada.
    * Muestra un **Shot Chart** visual de las zonas mencionadas.
    * El usuario puede refinar: *"Fíltralo solo para bases (guards)"*.

## 5. Características Principales y Requisitos Funcionales (The "What")

### A. Interfaz de Chat (Natural Language Querying)
* El **input** principal es una barra de búsqueda/chat prominente.
* Debe aceptar lenguaje coloquial, errores tipográficos en nombres de jugadores (ej. "Miciic") y sinónimos (ej. "Puntos" = "Pts" = "Anotación").

### B. Visualización Generativa
* Las respuestas no pueden ser solo texto. El sistema debe decidir la mejor forma de mostrar el dato:
    * Comparación de 2 jugadores -> **Tabla lado a lado**.
    * Tendencia temporal -> **Gráfico de líneas (Line Chart)**.
    * Distribución de tiro -> **Shot Chart** (Fase Pro).

### C. Transparencia y Confianza (Anti-Hallucination)
* Si la IA no está segura, debe preguntar para aclarar, no inventar.
* Cada respuesta debe citar la fuente implícita (ej. "Datos oficiales de Euroleague.net").
* Debe mostrar la consulta interpretada (ej. "Mostrando datos para la temporada 2023-2024").

### D. Modelo Freemium (Tiered Access)
* **Experiencia Free (MVP):** Acceso ilimitado al motor de IA, pero restringido a **estadísticas básicas** (puntos, rebotes, asistencias, clasificaciones).
* **Experiencia Pro:** Desbloqueo de acceso a **Estadísticas Avanzadas y Espaciales** (Shot Charts, PER, Win Shares).

### E. Experiencia de Usuario (UX/UI) Específica y Comportamiento de IA

* **Onboarding "Lienzo en Blanco":**
    * Al cargar la aplicación sin historial, se deben mostrar **3-4 "Chips" de sugerencias** rotativas (ej: "Líderes de anotación", "Récord del Real Madrid", "Comparar bases").
    * Objetivo: Reducir la carga cognitiva inicial y educar al usuario sobre el alcance del MVP.

* **Gestión de Latencia (Cold Start):**
    * Debido a la infraestructura serverless (Render Free Tier), el primer arranque tras inactividad puede demorar hasta 30s.
    * Requisito: Si la respuesta tarda más de 3 segundos, la UI debe mostrar un estado específico de **"Despertando al Agente..."** o **"Calentando motores..."** con un micro-copy amigable, diferenciándolo de la carga habitual para evitar frustración.

* **Continuidad Conversacional (Memoria):**
    * El sistema debe soportar **preguntas de seguimiento** (Follow-up) básicas.
    * Ejemplo: Si el usuario pregunta "Puntos de Micic" y seguidamente "¿Y de Larkin?", el sistema debe inferir el contexto ("Puntos") de la interacción anterior usando el historial del chat.

* **Loop de Feedback:**
    * Cada respuesta generada debe incluir controles discretos de **Válido/Inválido** (Thumbs up/down).
    * Esto servirá para auditar la calidad del Text-to-SQL y detectar alucinaciones sin interrumpir el flujo del usuario.

### F. Gestión de Límites, Errores y Persistencia

* **Manejo de Límites (Quota Exceeded):**
    * **Trigger:** Cuando el sistema recibe un error 429 o detecta que se ha alcanzado el límite de 50 consultas diarias (Free Tier OpenRouter).
    * **Comportamiento UI:** Mostrar un mensaje no intrusivo pero claro: *"¡Has agotado tus consultas diarias! Vuelve mañana para más estadísticas gratis o actualiza a Pro para acceso ilimitado."*
    * **Acción:** Bloquear el input de chat hasta el reset del día siguiente.

* **Intercepción de Consultas Pro (Upsell):**
    * **Trigger:** Un usuario Free solicita datos avanzados (ej. "Shot chart de Larkin" o "Puntos desde la esquina").
    * **Comportamiento UI:** El sistema identifica la intención "Pro", pero en lugar de fallar, responde: *"Esa consulta requiere acceso a datos espaciales avanzados. Actualiza a Pro para visualizar shot charts."*
    * **Componente:** Incluir un botón/CTA de "Ver planes" junto al mensaje.

* **Persistencia de Sesión:**
    * Utilizar `localStorage` para guardar el historial de chat del usuario.
    * Al recargar la página, el usuario debe ver su última conversación, evitando la sensación de "pérdida de contexto" si refresca por error.

* **Estados de Progreso Granulares (Feedback Loop):**
    * En lugar de un *spinner* genérico, mostrar etiquetas de estado cambiantes para mantener la atención durante latencias medias:
        1. *"Interpretando pregunta..."* (LLM processing)
        2. *"Consultando base de datos..."* (SQL execution)
        3. *"Generando gráficos..."* (Data rendering)
    * **Timeout:** Si el proceso supera los 60s, mostrar error amigable: *"El árbitro está revisando la jugada (Timeout). Por favor, intenta una pregunta más simple."*

## 6. Definición del Éxito (Outcome Metrics)

1.  **Time-to-Insight:** El usuario debe obtener el dato visualizado en menos de 5 segundos desde que termina de escribir la consulta.
2.  **Query Success Rate:** Porcentaje de preguntas que devuelven un resultado válido (SQL ejecutable) frente a mensajes de error/"No entiendo".
3.  **Retention:** Usuarios que vuelven a usar la herramienta después de la primera consulta (indicador de que el hábito de "preguntar" sustituye al hábito de "filtrar").
4.  **Shareability:** Frecuencia con la que los usuarios toman capturas de pantalla de los gráficos generados para compartirlos externamente (viralidad).

## 7. Restricciones y Límites
* **Alcance MVP:** Solo datos de la Euroliga actual (o últimas temporadas recientes). No NBA, no ligas domésticas por ahora.
* **Datos:** Nos basamos exclusivamente en datos oficiales estructurados. No hacemos *scraping* de narrativas de noticias o rumores.
* **Actualización de Datos:** Los datos se actualizan diariamente (una vez al día). El MVP **no incluye datos en tiempo real** del partido que está ocurriendo en ese momento. Las consultas durante un partido se refieren a estadísticas históricas, comparativas y acumuladas de temporada (ej. "¿Quién tiene mejor % de tiros libres esta temporada?"), no a estadísticas del partido en directo.
* **Dispositivo:** Mobile-first. La mayoría de las consultas ocurrirán en "segunda pantalla" mientras se ve un partido, consultando estadísticas históricas para enriquecer la experiencia de visualización.
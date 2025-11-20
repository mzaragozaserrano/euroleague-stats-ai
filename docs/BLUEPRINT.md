# Análisis de Viabilidad y Arquitectura Estratégica: Aplicación de Estadísticas de Euroliga con IA

## I. Análisis de Viabilidad de Mercado: El Nicho de la Euroliga

### A. La Brecha de Demanda: Evidencia de la Frustración del Usuario en el Mercado de Estadísticas de la Euroliga

La viabilidad de un nuevo producto se mide fundamentalmente por la existencia de un problema claro y una demanda articulada por una solución. En el caso de las estadísticas avanzadas de la Euroliga, la evidencia de una demanda de mercado frustrada es significativa y se encuentra documentada en foros públicos de aficionados.

El análisis de las discusiones en comunidades especializadas como r/Euroleague revela un patrón recurrente: los aficionados, a menudo con experiencia en el ecosistema de datos de la NBA, buscan herramientas equivalentes para la Euroliga y expresan su insatisfacción con la oferta actual. Las consultas son directas: "¿Cuáles son las mejores páginas web para encontrar estadísticas de la Euroleague?". Los usuarios mencionan explícitamente estar "acostumbrados a usar Basketball Reference" (el estándar de oro para las estadísticas de la NBA) y lamentan que las herramientas existentes "directamente no tienen estadísticas" comparables o que el sitio web oficial de la Euroliga es "un poco aburrido".

Esta frustración no se limita a las estadísticas de superficie. Los usuarios buscan activamente métricas avanzadas y específicas que actualmente son inaccesibles. Por ejemplo, existe un deseo explícito de encontrar datos granulares como **"puntos en transición"** o métricas situacionales como "cuántos partidos se van a la prórroga", datos que actualmente obligarían a un análisis manual.

El tipo de consultas indica que el mercado objetivo no está compuesto por aficionados casuales. El usuario que busca "puntos en transición" o que se queja de la falta de herramientas al nivel de Basketball-Reference es un consumidor de datos sofisticado. Este segmento —que incluye a aficionados acérrimos (*die-hard fans*), jugadores de ligas *fantasy* y analistas de apuestas— valora la profundidad, la precisión y la accesibilidad de los datos por encima de todo.

La validación de mercado más sólida proviene de la observación de que este vacío es tan doloroso que los propios miembros de la comunidad, que poseen habilidades técnicas, están intentando activamente construir sus propias soluciones. En los mismos hilos de discusión donde los usuarios se quejan, otros promocionan sus proyectos independientes. Ejemplos notables incluyen al usuario 'CappeMugiwara' presentando su sitio **hackastat.eu** como una solución para estadísticas avanzadas de la Euroliga y la Eurocup, y al usuario 'International_Bus339' construyendo **Oddsballer**, una herramienta específica para el seguimiento de líneas de apuestas y tendencias de jugadores en la Euroliga.

Este fenómeno representa una validación de mercado de "abajo hacia arriba" (*bottom-up*) de la más alta calidad. No se trata de una demanda hipotética que requiera la creación de un nuevo mercado. Es un mercado existente y desatendido donde los clientes potenciales ya están invirtiendo su propio tiempo y recursos para fabricar soluciones provisionales. El producto propuesto no estaría creando una demanda, sino que estaría satisfaciendo una que ya existe, es vocal y está demostrablemente activa.

### B. La Oportunidad del NLP: Por Qué las Consultas en Lenguaje Natural son el Diferenciador Clave

El producto propuesto no es simplemente "otro sitio web de estadísticas"; su característica central, la búsqueda mediante IA, lo posiciona como una herramienta de productividad fundamentalmente diferente que redefine el flujo de trabajo del usuario.

Las herramientas actuales que los usuarios comparten, como hackastat.eu, 3stepsbasket.com y proballers.com, operan bajo un paradigma de navegación de "filtros y tablas". Un análisis detallado de estas plataformas confirma esta limitación:

* **Hackastat.eu:** Ofrece estadísticas avanzadas, pero la navegación se basa estrictamente en clics a través de categorías predefinidas (Equipos, Jugadores, Alineaciones).
* **Proballers.com:** Proporciona perfiles y clasificaciones, pero la interacción se limita a filtros y tablas estandarizadas.
* **Data4Basket:** Se centra en visualizaciones interactivas, pero su funcionalidad principal se basa en "filtros, rankings, plots y herramientas de comparación predefinidas".

Ninguno de estos competidores indirectos ofrece una interfaz de consulta en lenguaje natural (NLP). Este paradigma de "filtros" impone una fricción significativa. Para responder una pregunta como *"Comparativa de puntos por partido entre Micic y Larkin"*, el flujo de trabajo actual del usuario requiere:

1.  Navegar a la sección de "Estadísticas de Jugadores".
2.  Utilizar un filtro o buscador para encontrar a Vasilije Micic.
3.  Absorber o anotar sus estadísticas.
4.  Regresar y buscar a Shane Larkin.
5.  Absorber o anotar sus estadísticas.
6.  Realizar la comparación mental o manualmente.

Una consulta más compleja, como *"Dame los 5 jugadores que más puntos anotan desde la esquina del triple derecho"*, es **imposible** de responder en **cualquier** plataforma existente.

La innovación central de la arquitectura de IA propuesta es su capacidad para resolver consultas **composicionales**. Estas son preguntas que combinan múltiples filtros (ej. tipo de tiro = triple), uniones de datos (ej. tabla de jugadores + tabla de *shot-charts*) y agregaciones (ej. "top 5"), que son computacionalmente inviables de pre-calcular en una interfaz de filtros estándar.

El valor de la IA, por lo tanto, no es un artilugio; es la **velocidad** y la **posibilidad**. Condensa un proceso de investigación manual de diez minutos (o uno imposible) en una sola consulta de cinco segundos. Esto conduce a una "inversión del flujo de trabajo". Las herramientas actuales obligan al usuario a **buscar datos** para **luego encontrar una respuesta**. La plataforma propuesta permite al usuario **preguntar la respuesta** y delega a la IA la tarea de **encontrar los datos**. Esta inversión representa una mejora de 10x en la experiencia del usuario (UX), sentando las bases para un producto disruptivo con una ventaja competitiva defendible.

### C. Validación del Concepto: El Auge de las Interfaces de Datos NLP en el Deporte

El modelo de producto propuesto (una interfaz de lenguaje natural sobre una base de datos deportiva estructurada) no es una especulación teórica. Es una tendencia emergente y probada, tanto en mercados deportivos con mayor madurez de datos (como Estados Unidos) como en el ámbito de la investigación académica.

Existen múltiples análogos en el mercado de la NBA que validan esta funcionalidad exacta:
* **Definitive.io:** Se comercializa como una "herramienta de consulta estadística basada en IA para datos de la NBA".
* **Otros desarrolladores:** Están construyendo activamente aplicaciones de chat que utilizan técnicas de Generación Aumentada por Recuperación (RAG) sobre bases de datos de estadísticas de la NBA.
* **IBM & Watsonx:** Utilizando watsonx con la UFC, permite a los comentaristas y editores "extraer ideas usando lenguaje natural" a través de pipelines de Texto-a-SQL.

Aún más significativa es la validación académica reciente, que confirma la viabilidad técnica de la arquitectura central propuesta. El *paper* de investigación **"SPORTSQL: An Interactive System for Real-Time Sports Reasoning and Visualization"** describe un sistema que es funcionalmente idéntico al producto propuesto. SportSQL es un sistema interactivo para "consultas en lenguaje natural y visualización de datos deportivos dinámicos" que "traduce las preguntas del usuario en SQL ejecutable" sobre una base de datos en vivo y, de manera crucial, "genera una visualización" como salida. Proyectos similares, como "SoccerRAG", aplican los mismos principios (NLP-a-SQL) a los datos de fútbol.

Desde una perspectiva estratégica, esto posiciona al producto dentro de un modelo de **fast follower** (seguidor rápido). La estrategia consiste en tomar un modelo de negocio probado (NLP para estadísticas deportivas, validado en el mercado estadounidense) y aplicarlo a un dominio o geografía desatendida (la Euroliga). Esto reduce drásticamente el riesgo de mercado, ya que la pregunta "¿la gente querrá esto?" ha sido respondida afirmativamente. Además, la existencia de *papers* como SportSQL proporciona una ventaja técnica. Significa que una comunidad de investigación ya está abordiendo y resolviendo los problemas arquitectónicos más difíciles (ej. manejo de datos dinámicos, razonamiento temporal, generación de SQL complejo y visualización de salidas). El producto no se construiría en un vacío técnico, sino sobre una base de investigación emergente y validada.

---

## II. Análisis del Panorama Competitivo

### A. El Competidor Directo (Ausente): Statmuse como Modelo de Éxito y Advertencia

El análogo funcional más cercano al producto propuesto, y el competidor más relevante a nivel estratégico, es **Statmuse**. Su análisis proporciona la validación de mercado más sólida y, al mismo tiempo, la advertencia estratégica más importante.

Statmuse es una plataforma de gran éxito definida como una "base de datos de estadísticas deportivas que puede responder a consultas en lenguaje natural". Su cobertura se centra exclusivamente en las ligas norteamericanas (NBA, NFL, MLB, NHL, etc.). Ha construido toda su identidad de marca y adquisición de usuarios en torno a la potencia de sus consultas de lenguaje natural, que a menudo se utilizan para generar contenido viral en redes sociales. La ausencia total de cobertura de la Euroliga por parte de Statmuse define la brecha de mercado principal y la oportunidad para este proyecto.

Recientemente, Statmuse introdujo una advertencia estratégica crítica: movió la mayoría de sus resultados (más allá de las 10 primeras respuestas) detrás de un muro de pago llamado "Statmuse+", con un precio de $20 por mes. Esta decisión generó una reacción negativa significativa y vocal por parte de su base de usuarios.

Para este proyecto, la estrategia de precios de Statmuse es una noticia excepcionalmente positiva por dos razones:
1.  **Validación de Valor:** Establece un precedente de precio *premium* ($20/mes) para la funcionalidad de NLP sobre estadísticas. Esto valida que los usuarios perciben un alto valor en esta capacidad, muy por encima de las herramientas de filtro gratuitas.
2.  **Oportunidad de Marketing:** La reacción negativa proporciona un ángulo de marketing y posicionamiento inmediato. El producto de la Euroliga puede entrar en el mercado con un precio significativamente más bajo (ej. €5-€10/mes) y posicionarse como la alternativa justa, centrada en el usuario y enfocada en Europa, capitalizando la mala voluntad generada por Statmuse.

Finalmente, el análisis de cómo otras herramientas interactúan con Statmuse revela pistas arquitectónicas. Se le describe no solo como un LLM, sino como un "motor de búsqueda de lenguaje natural especializado" que puede ser utilizado como una herramienta por un "agente" de LLM más grande (como GPT-3) para planificar y delegar búsquedas. Esto refuerza la conclusión de que un LLM por sí solo no puede responder a estas consultas de manera confiable. Debe ser **aumentado** (RAG) y conectado a una base de datos estructurada y especializada (Text-to-SQL).

### B. El Ecosistema de Competidores Indirectos (Filtros y Paneles)

El mercado actual de herramientas de estadísticas de la Euroliga no está vacío, pero está poblado exclusivamente por competidores indirectos que operan en un paradigma tecnológico diferente. Ninguno compite con la funcionalidad principal de NLP.

* **Hackastat.eu:** Es el competidor indirecto más referenciado y apreciado por la comunidad. Ofrece un valor genuino a través de estadísticas avanzadas (como PER, Usg%, Win Shares) para la Euroliga y la Eurocup. Sin embargo, su análisis confirma que la navegación se basa estrictamente en clics a través de categorías predefinidas (Equipos, Jugadores, Alineaciones), sin capacidad de consulta en lenguaje natural.
* **Proballers.com:** Cubre una amplia gama de ligas, incluida la Euroliga, pero su enfoque es más superficial. La interfaz se limita a categorías predefinidas como "Líderes", "Récords", "Calendario" y "Clasificación". Es útil para perfiles de jugadores individuales, pero carece de herramientas de análisis profundo o comparativo.
* **Data4Basket:** Se promociona como una plataforma de "estadística avanzada" con "visualizaciones interactivas". Al igual que Hackastat, su funcionalidad se basa en "filtros, rankings, plots y herramientas de comparación predefinidas". Su estrategia de monetización (un Plan PRO) valida que los usuarios están dispuestos a pagar por datos avanzados, pero no compite en la interfaz de NLP.
* **Oddsballer:** Esta herramienta representa una validación de un nicho específico. Se enfoca exclusivamente en el mercado de apuestas, rastreando el rendimiento de los jugadores contra las líneas de apuestas (over/under de puntos, rebotes, asistencias). Su existencia y su modelo de suscripción validan aún más que los segmentos de usuarios de alto valor (apostadores) **pagarán** por datos de la Euroliga que les ahorren tiempo o les den una ventaja analítica.

La diferencia fundamental en la experiencia del usuario (UX) es clara: todos estos competidores obligan al usuario a "buscar datos" manualmente. El producto propuesto les permite "hacer una pregunta". La competencia no es sobre quién tiene **más** datos (probablemente todos se obtienen de fuentes similares), sino sobre quién proporciona el **acceso** más rápido y flexible a esos datos. Es poco probable que los operadores establecidos como Hackastat o Proballers puedan simplemente "añadir IA" para competir. Sus arquitecturas de producto actuales (probablemente aplicaciones web monolíticas o CRUD estándar) no están diseñadas para un pipeline de IA de Text-to-SQL. La arquitectura propuesta (FastAPI, Neon, RAG) está **diseñada desde cero** para esta funcionalidad. Esto crea un foso técnico (una ventaja competitiva) que es difícil y costoso de replicar para los competidores existentes.

### C. Tabla: Matriz de Análisis Competitivo

| Competidor | Cobertura (Liga) | Funcionalidad Principal | ¿Ofrece NLP? | Modelo de Precios | Debilidad/Oportunidad Clave |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Statmuse** | NBA, NFL, MLB (EE. UU.) | Consulta NLP | Sí | Suscripción ($20/mes) | No cubre la Euroliga (Su brecha de mercado). |
| **Hackastat.eu** | Euroliga, Eurocup, LBA | Paneles Avanzados / Filtros | No | Gratis (aparentemente) | Sin NLP. UX de "búsqueda manual" intensiva. |
| **Proballers.com** | Global (incl. Euroliga) | Perfiles / Récords | No | Gratis | Datos superficiales. Sin análisis profundo. |
| **Data4Basket** | Múltiples (incl. Euroliga) | Visualizaciones / Filtros | No | Freemium (con Plan PRO) | Sin NLP. Enfocado en "juegos". |
| **Oddsballer** | Euroliga, NBA | Apuestas (Over/Under) | No | Suscripción | Nicho muy específico (apuestas). Valida el pago. |
| **[Tu Producto]** | Euroliga (MVP) | Consulta NLP (Estadísticas Básicas) | **Sí (Core)** | Gratis (MVP) / Freemium (Post-MVP) | N/A |

---

## III. Viabilidad Financiera y Modelo de Negocio Sostenible

### A. Desglose de Costos Operativos: La Economía del Stack Serverless para un MVP gratuito

La solicitud de un MVP de 3 semanas sin costo es un objetivo de ingeniería, no solo de negocio. Requiere explotar estratégicamente los niveles gratuitos del stack tecnológico propuesto, aceptando sus limitaciones inherentes como parte del *trade-off* del MVP. A diferencia del SaaS tradicional, una aplicación de IA tiene un **costo marginal variable** por cada consulta. Un modelo "gratuito" sin control es insostenible. Sin embargo, para un MVP de 3 semanas, los niveles gratuitos están diseñados precisamente para este propósito.

#### A.1. Costos de Inferencia de IA (OpenRouter)
* **Nivel Gratuito:** Limita a los usuarios a **50 solicitudes por día**.
* **Viabilidad del MVP:** Para un desarrollo de 3 semanas y una demostración inicial, 50 consultas de IA al día son **suficientes** para las pruebas y la validación. Sin embargo, es insuficiente para un lanzamiento público. Esto debe ser aceptado como una limitación del MVP.

#### A.2. Costos de Base de Datos (Neon)
* **Nivel Gratuito:** Ofrece **0.5 GB de almacenamiento**.
* **Viabilidad del MVP:** Un conjunto de datos de estadísticas **básicas** (promedios por partido, totales de temporada, récords de equipo) para la Euroliga, incluso abarcando varias temporadas, es esencialmente un conjunto de datos de texto y números que encajará cómodamente dentro del límite de 0.5 GB.
* **Estrategia de Monetización:** La restricción de 0.5 GB **define** la hoja de ruta. Los datos complejos y voluminosos, como las coordenadas X/Y de cada tiro (*shot-charts*), superarán rápidamente este límite. Por lo tanto, el conjunto de datos de "estadísticas avanzadas/espaciales" se convierte en el **activo** que se desbloquea con el plan de pago (Post-MVP), que financiaría la actualización al plan "Launch" de Neon (pago por uso).

#### A.3. Costos de Alojamiento (Render)
* **Nivel Gratuito:** Los servicios web gratuitos se "suspenden" (*spin down*) después de 15 minutos de inactividad.
* **Viabilidad del MVP:** Esto es aceptable para un MVP de 3 semanas. Significa que la **primera** carga de la aplicación por parte de un usuario (o una carga después de 15 minutos de inactividad) será lenta. Las solicitudes posteriores serán rápidas. Este es un *trade-off* no monetario necesario para lograr el objetivo de un MVP gratuito. El plan "Starter" de pago ($9/mes por servicio) elimina este problema y sería la primera actualización Post-MVP.

### B. Tabla: Escenarios de Costos Mensuales Proyectados (MVP vs. Crecimiento)

| Componente | Plan "MVP - 3 Semanas" | Plan "Pro" (Post-MVP, Baja Tracción) |
| :--- | :--- | :--- |
| **Render (FastAPI)** | $0 (Nivel Gratuito) | $9/mes (Plan Starter) |
| **Render (Next.js)** | $0 (Nivel Gratuito) | $9/mes (Plan Starter) |
| **Neon (Postgres)** | $0 (Nivel Gratuito, límite 0.5 GB) | $5/mes (Mínimo Plan Launch) |
| **OpenRouter (LLM)** | $0 (Nivel Gratuito, límite 50 reqs/día) | $20/mes (Estimación de pago por uso) |
| **Total Estimado** | **$0** | **~$43/mes** |
| **Limitaciones Clave** | Carga inicial lenta (Spin-Down). Límite de 0.5 GB (solo stats básicas). Límite de 50 consultas/día. | Sin "spin-down". Almacenamiento para stats avanzadas. Límite de consultas de IA más alto. |

### C. Estrategia de Monetización Recomendada: El Modelo Freemium Alineado al MVP

La nueva estrategia propuesta es un modelo "Freemium" mucho más fuerte y sostenible.

**Nivel Gratuito (El MVP):**
* **Funcionalidad:** **Acceso completo** al motor de IA Text-to-SQL.
* **Limitación:** El motor de IA solo puede consultar la base de datos de **estadísticas básicas** (el conjunto de datos < 0.5 GB).
* **Justificación Económica:** Este enfoque es viable porque se mantiene dentro de **todos** los límites del nivel gratuito (Render, Neon, OpenRouter). Permite a los usuarios experimentar el poder de la funcionalidad *core* (la consulta NLP) sin costo para el operador (aparte de los límites de uso muy bajos de OpenRouter).

**Nivel "Pro" (El Producto Post-MVP, de Pago):**
* **Propuesta de Valor:** "Desbloquea Estadísticas Avanzadas y Espaciales".
* **Funcionalidad:** El **mismo** motor de IA ahora consulta un conjunto de datos mucho más rico, que incluye datos de *shot-charts*, estadísticas avanzadas (PER, Win Shares, etc.) y análisis espaciales (consultas de "esquina del triple").
* **Justificación Económica:** Este modelo es perfectamente sostenible. El ingreso de la suscripción (ej. €5-€8/mes) financia directamente las actualizaciones de infraestructura necesarias para ofrecer la función:
    * **Actualización de Neon:** Para almacenar los datos de *shot-charts* (> 0.5 GB).
    * **Actualización de Render:** Para eliminar el "spin-down" y ofrecer una experiencia *premium*.
    * **Actualización de OpenRouter:** Para manejar un volumen de consultas de IA mucho mayor que el límite de 50/día.

Este modelo alinea los incentivos: los usuarios gratuitos validan el producto con costo cero, y los usuarios de pago financian la infraestructura exacta que sus funciones avanzadas requieren.

---

## IV. Análisis Profundo de la Arquitectura Técnica y del Stack

### A. Validación del Stack de Servicios: FastAPI, Neon/SQLAlchemy, y Next.js/Recharts

El stack tecnológico propuesto es moderno, altamente escalable y una excelente elección para este proyecto. Los componentes están bien documentados y diseñados para trabajar en conjunto.

* **FastAPI + Neon/Postgres:** Existen numerosos tutoriales, guías y repositorios de ejemplo que demuestran la conexión de FastAPI a una base de datos Neon (PostgreSQL) utilizando ORMs como SQLAlchemy o SQLModel (que se basa en SQLAlchemy). Es una combinación probada para construir APIs de datos de alto rendimiento.
* **Next.js + Recharts/Chart.js:** Esta es una pila estándar de la industria para construir interfaces de usuario y paneles de control dinámicos e interactivos. Permite la creación de las visualizaciones de datos (gráficos) requeridas por la solicitud del usuario.

Sin embargo, hay una configuración técnica crítica, no obvia, que es esencial para la estabilidad de esta arquitectura *serverless*. El desafío surge de la combinación de un servicio de aplicación *serverless* (FastAPI en Render, que puede escalar a cero o reiniciarse) y una base de datos *serverless* (Neon, que también se escala a cero).

El *pooling* de conexiones de base de datos tradicional, como el `QueuePool` por defecto de SQLAlchemy, asume un servidor de aplicaciones persistente que mantiene un "pool" de conexiones listas para usar. En este stack, la base de datos de Neon puede "dormirse" (scale-to-zero) después de 5 minutos. El *pool* de conexiones dentro de la aplicación FastAPI, sin embargo, seguirá manteniendo referencias a estas conexiones, que ahora están "caducadas" (*stale*) o muertas. Cuando una nueva solicitud de usuario llega a FastAPI, SQLAlchemy intentará tomar una conexión de su *pool*, recibirá una conexión muerta y la aplicación fallará con un error de base de datos.

La **solución crítica** es **deshabilitar** el pooling de conexiones del lado de la aplicación y delegar toda la gestión del pool al proveedor de la base de datos.
* **Implementación:** En la configuración del motor de SQLAlchemy, se debe establecer `poolclass=NullPool`.
* **Efecto:** Esto le dice a SQLAlchemy que no mantenga ningún pool. En su lugar, cada vez que la aplicación necesita una conexión, abre una nueva y la cierra cuando termina.
* **Por qué funciona:** Esta estrategia normalmente sería desastrosa, pero Neon proporciona un **pooler de conexiones externo** (basado en pgBouncer) que se sitúa entre la aplicación y la base de datos. Este pooler está diseñado para manejar miles de conexiones efímeras (hasta 10,000). Al usar `NullPool`, la aplicación delega la gestión del pool al servicio de Neon, que está optimizado para este entorno *serverless*, garantizando estabilidad y escalabilidad. Esta configuración es absolutamente esencial para que la arquitectura funcione de manera fiable en producción.

### B. El Núcleo de IA: Diseño del Motor Text-to-SQL + RAG (Enfoque MVP)

El usuario identificó correctamente la necesidad de una arquitectura dual: un LLM para Text-to-SQL (vía OpenRouter) y un sistema RAG (con un modelo de embedding como Qwen3). Esta es la arquitectura correcta, ya que un LLM por sí solo no puede generar SQL preciso sin contexto. El desafío principal de Text-to-SQL es que los LLM "alucinan": inventan nombres de tablas, columnas o valores que no existen. El propósito de la Generación Aumentada por Recuperación (RAG) en este contexto es anclar el LLM a la realidad del esquema de la base de datos.

**Flujo de Trabajo para el MVP (Estadísticas Básicas):**
1.  **Indexación (Offline):** **No** se vectorizan las filas de estadísticas. En su lugar, se vectoriza el **esquema de la base de datos** de estadísticas básicas. Esto incluye: nombres de tablas (ej. `player_stats_basic`), descripciones de columnas (ej. "ppg es puntos por partido"), y **ejemplos de consultas SQL** funcionales. Esto se almacena en pgVector dentro del nivel gratuito de Neon.
2.  **Consulta (Online):**
    * a. El usuario pregunta: "Comparativa de puntos por partido entre Micic y Larkin".
    * b. El RAG (usando Qwen3) convierte esa pregunta en un vector y busca en la base de datos de vectores (pgVector en Neon) los fragmentos de esquema y ejemplos más relevantes.
    * c. El RAG recupera contexto como: "Esquema: `player_stats_basic(player_id, ppg,...)`", "Esquema: `players(id, full_name)`", "Ejemplo: `SELECT... FROM player_stats_basic JOIN players...`".
    * d. La consulta al LLM (Claude 3.5 Sonnet, a través de OpenRouter) se "aumenta" con este contexto: "Contexto Relevante: [Esquema y ejemplos recuperados]. Pregunta del Usuario: '...'. Por favor, genera la consulta SQL.".

**Hoja de Ruta Post-MVP (La Característica "Pro"):**
La consulta de ejemplo *"Dame los 5 jugadores que más puntos anotan desde la esquina del triple derecho"* debe ser **explícitamente** excluida del MVP de 3 semanas. Esta consulta introduce una complejidad mucho mayor.
* **El Problema:** "La esquina del triple derecho" es una **consulta geométrica o espacial** (ej. `WHERE shot_x > 20 AND shot_y < 5`).
* **La Incompatibilidad:** pgVector **no puede** manejar eficientemente este tipo de consulta espacial.
* **La Solución (Post-MVP):** La extensión **PostGIS**, que también es compatible con Neon, está diseñada para esto.
* **La Oportunidad de Monetización:** La implementación de PostGIS y la ingesta de los voluminosos datos de *shot-charts* (que superarán los 0.5 GB) se convierte en la actualización técnica central que justifica el "Plan Pro". El foso defensivo del producto, por lo tanto, no es simplemente Text-to-SQL. Es **Text-to-Spatial-SQL**.

### C. Fuente de Datos: API Oficial de Euroleague como Base del Sistema

**La Validación Más Importante: Acceso a Datos Oficiales y Estructurados**

El éxito del producto depende fundamentalmente de la disponibilidad de datos fiables y actualizados. La viabilidad técnica del proyecto se confirma con el acceso a la **API oficial de Euroleague** ([https://api-live.euroleague.net/swagger/index.html](https://api-live.euroleague.net/swagger/index.html)), que proporciona datos estructurados en formato JSON a través de endpoints RESTful.

**Endpoints Clave Disponibles:**

La API de Euroleague ofrece acceso a los siguientes tipos de datos, que se alinean perfectamente con los requisitos del MVP y la hoja de ruta Post-MVP:

1. **`/teams`**: Información detallada de equipos (nombres, códigos, imágenes, plantillas).
2. **`/players`**: Perfiles de jugadores (datos biográficos, posición, equipo actual).
3. **`/games`**: Calendario de partidos, resultados, box scores básicos.
4. **`/standings`**: Clasificaciones actualizadas por competición y temporada.
5. **`/playerstats`**: Estadísticas agregadas por jugador (puntos, rebotes, asistencias, etc.).
6. **`/teamstats`**: Estadísticas agregadas por equipo (ofensivas, defensivas, eficiencia).

**Mapeo de Datos a las Fases del Producto:**

| Fase del Producto | Endpoints Necesarios | Tamaño Estimado de Datos | Viabilidad con Neon Gratuito (0.5 GB) |
| :--- | :--- | :--- | :--- |
| **MVP (Estadísticas Básicas)** | `/teams`, `/players`, `/games`, `/playerstats`, `/standings` | < 200 MB (varias temporadas de box scores y promedios) | **Viable** |
| **Post-MVP "Pro" (Estadísticas Espaciales)** | Los anteriores + endpoints de *play-by-play* (si están disponibles) o fuentes alternativas para coordenadas X/Y de tiros | > 1 GB (datos de shot-charts con coordenadas) | Requiere Plan de Pago |

**Consideraciones Técnicas Críticas:**

* **Autenticación:** La API de Euroleague puede requerir autenticación (ej. API key en headers). Durante la fase de implementación del ETL, se debe verificar si la API es pública o requiere registro. Si requiere credenciales, estas deben almacenarse de forma segura como **secretos de GitHub** (para el ETL con GitHub Actions) o variables de entorno en Render.
* **Rate Limits (Límites de Uso):** No se ha identificado documentación pública sobre rate limits específicos. Es fundamental realizar pruebas iniciales del ETL para identificar cualquier limitación de tasa (ej. solicitudes por minuto/hora). Si existen límites estrictos, el script de ETL debe implementar:
    * **Retroceso exponencial** (*exponential backoff*) para manejar errores HTTP 429 (Too Many Requests).
    * **Caché local** de respuestas para evitar solicitudes redundantes durante el desarrollo.
* **Actualización de Datos:** La frecuencia de actualización de los datos en la API de Euroleague determina la frecuencia óptima del ETL. Para un MVP:
    * **Diario (00:00 UTC)** es suficiente para estadísticas de temporada y clasificaciones.
    * Para datos "en vivo" (ej. durante un partido), se requeriría un enfoque de *polling* más frecuente o webhooks (fuera del alcance del MVP).
* **Datos de Shot-Charts (Desafío Post-MVP):** La disponibilidad de coordenadas X/Y de tiros en la API oficial no está confirmada. Si la API no proporciona estos datos:
    * **Plan B:** Investigar APIs alternativas o fuentes de datos de la comunidad (ej. scraping ético del sitio web oficial con permisos, o servicios de datos deportivos de terceros como Synergy Sports o InStat).
    * **Implicación Estratégica:** Este desafío de datos refuerza la validez del modelo Freemium. Si los datos espaciales son difíciles de obtener, esto los convierte en un **activo exclusivo** y justifica aún más el precio del "Plan Pro".

**Validación de Viabilidad:**

La existencia de la API oficial de Euroleague es una señal de viabilidad excepcionalmente positiva. Confirma que:
1. Los datos existen en un formato estructurado y accesible (JSON).
2. No se requiere *scraping* de páginas web (más frágil y potencialmente prohibido por los términos de servicio).
3. La Euroleague ha invertido en una infraestructura de datos para desarrolladores, lo que sugiere apertura a aplicaciones de terceros (aunque siempre se deben respetar los términos de uso).

### D. Arquitectura del Pipeline ETL: GitHub Actions (Cron) vs. Cron Jobs Nativos de Render

El producto requiere un pipeline de Extracción, Transformación y Carga (ETL) diario que consuma la API de Euroleague e ingeste los datos en la base de datos Neon. Para el objetivo de un **MVP en 3 semanas**, la elección es clara.

**Opción 1: GitHub Actions (Cron) (Propuesta por el usuario):**
* **Costo:** Gratuito. El nivel gratuito de GitHub ofrece 2000 minutos de cómputo al mes, lo cual es más que suficiente para un ETL diario que probablemente dure unos pocos minutos.
* **Flujo de trabajo:** Se configura un trabajo cron en GitHub Actions (ej. `on: schedule: - cron: '0 0 * * *'` para ejecutar a medianoche UTC). El script de Python se ejecuta en el corredor de GitHub, consume la API de Euroleague (endpoints `/teams`, `/players`, `/playerstats`, etc.), transforma los datos (limpieza, normalización) y los carga directamente en la base de datos Neon usando SQLAlchemy.
* **Gestión de Secretos:** Las credenciales de la API de Euroleague (si son necesarias) y la cadena de conexión de Neon se almacenan como **secretos de GitHub**, accesibles de forma segura por el workflow de Actions.
* **Recomendación:** Esta es la opción correcta para el MVP.

**Opción 2: Render Cron Jobs (Nativa de la plataforma):**
* **Costo:** Un servicio de Cron Job de Render que se ejecute de manera fiable requeriría un plan de pago (ej. "Starter" de $9/mes) para evitar fallos aleatorios o limitaciones.
* **Recomendación:** Esta es una solución más robusta e integrada para la **producción** (Post-MVP), pero implicaría un costo.

---

## V. Recomendaciones Estratégicas y Hoja de Ruta del Producto

### A. Fase 1 (MVP en 3 Semanas): Validación del Motor de IA Básico
* **Objetivo:** Lanzar un producto funcional en 3 semanas que valide el motor de IA principal (Text-to-SQL) y el interés del mercado.
* **Acciones Clave:**
    * **ETL:** Construir el pipeline ETL usando **GitHub Actions (Cron)**. Consumir la **API oficial de Euroleague** (endpoints `/teams`, `/players`, `/games`, `/playerstats`, `/standings`) para ingestar **solo** estadísticas básicas (box score, promedios por partido, totales de temporada) en la base de datos Neon. Implementar gestión de errores y manejo de rate limits. Asegurarse de que el tamaño total de la BD se mantenga por debajo del límite de 0.5 GB.
    * **IA (RAG):** Construir el sistema RAG inicial. Usar Qwen3-Embedding para vectorizar el **esquema** de la base de datos de estadísticas básicas y los ejemplos de SQL, almacenándolos en pgVector.
    * **IA (Backend):** Implementar el backend de FastAPI con el "enrutador de modelos" (usando Claude 3 Haiku/Sonnet) a través de **OpenRouter (Nivel Gratuito)**, aceptando el límite de 50 consultas/día.
    * **Frontend y Despliegue:** Desplegar el frontend de Next.js y el backend de FastAPI en **Render (Nivel Gratuito)**. Aceptar el *trade-off* de la carga inicial lenta ("spin-down") como un costo no monetario para validar la idea.
* **Meta de Hito:** Responder de manera confiable a consultas **no espaciales** como: "Comparativa de puntos por partido entre Micic y Larkin".

### B. Fase 2 (Monetización): Lanzamiento del "Plan Pro" con Estadísticas Espaciales
* **Objetivo:** Introducir un plan de pago (Post-MVP) que financie la infraestructura necesaria para desbloquear la característica *killer* del producto: Text-to-Spatial-SQL.
* **Acciones Clave:**
    * **Desafío de Datos:** Adquirir datos fiables de *shot-charts* (coordenadas X/Y). Investigar si la API de Euroleague proporciona endpoints de *play-by-play* con datos espaciales. Si no están disponibles, explorar fuentes alternativas (APIs de terceros, scraping ético con permisos, o servicios de datos deportivos comerciales). Este es ahora el activo principal del plan de pago.
    * **Desafío Técnico (DB):** Actualizar a un plan de pago de **Neon**. Habilitar la extensión **PostGIS**. Ingestar los datos de coordenadas X/Y (que superarán el límite de 0.5 GB).
    * **Desafío de IA (RAG):** Actualizar el sistema RAG para reconocer lenguaje espacial (ej. "esquina", "poste bajo") y recuperar plantillas de consulta de PostGIS.
    * **Desafío de Infraestructura:** Actualizar los servicios de FastAPI y Next.js a los planes **Render "Starter"** para eliminar el "spin-down" y ofrecer una experiencia de usuario *premium* (sin carga lenta).
    * **Desafío de Costos de IA:** Actualizar a **OpenRouter (Pago por uso)** para manejar el aumento de consultas más allá del límite de 50/día.
* **Meta de Hito:** El "Plan Pro" (ej. €5-€8/mes) ya está disponible. Los usuarios de pago pueden ahora hacer la consulta de ejemplo: "Dame los 5 jugadores que más puntos anotan desde la esquina del triple derecho". Los ingresos de este plan cubren directamente los costos de Render, Neon y OpenRouter.

### C. Fase 3 (Expansión y Sostenibilidad): Optimización de Costos y Crecimiento
* **Objetivo:** Escalar la base de usuarios de pago de manera rentable y expandir la cobertura del producto.
* **Acciones Clave:**
    * **Optimización de Costos (Caché):** Implementar una capa de **caché** (ej. Render Redis). Si 100 usuarios hacen la misma pregunta (ej. "Máximos anotadores Euroliga 2025"), solo la primera consulta debe golpear la API del LLM y la base de datos. Las 99 restantes deben servirse instantáneamente desde el caché. Esto reduce drásticamente los costos de inferencia de IA.
    * **Optimización de Costos (IA):** Afinar continuamente el "enrutador" de modelos. Monitorear qué consultas fallan con el modelo barato (Haiku) y necesitan ser escaladas. El objetivo es maximizar la tasa de éxito del modelo más barato posible.
    * **Expansión de Contenido:** Utilizar los ingresos generados por el Nivel Pro para licenciar o adquirir conjuntos de datos para otras ligas solicitadas por los usuarios (ej. EuroCup, ACB, ligas domésticas).
    * **Estrategia de Mercado:** Utilizar la reacción negativa al precio de $20/mes de Statmuse como un pilar de marketing. Adquirir usuarios de forma agresiva posicionando el producto como la alternativa justa, potente y centrada en el baloncesto europeo que la comunidad ha estado pidiendo.

---

### Obras citadas (Selección Relevante)

* ¿Cuáles son las mejores páginas web para encontrar estadísticas de la Euroleague? - Reddit
* Advanced Stats? : r/Euroleague - Reddit
* Website/app with advanced stats for European leagues : r/Euroleague - Reddit
* Hackastat.eu - Advanced stats for everybody
* Proballers.com - Euroleague Scores and Stats
* SPORTSQL: An Interactive System for Real-Time Sports Reasoning and Visualization (arXiv)
* SoccerRAG: Multimodal Soccer Information Retrieval via Natural Queries (arXiv)
* StatMuse - App Store & Pricing Strategy Analysis
* FastAPI Documentation - SQL Databases
* Neon Guides - Building a High-Performance API with FastAPI
* OpenRouter Pricing & Documentation
* Render Pricing & Free Tier Documentation
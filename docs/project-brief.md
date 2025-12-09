# Project Brief: Euroleague AI Stats Agent

## 1. Overview
Una interfaz de inteligencia de datos para la Euroliga basada en lenguaje natural. Invertimos el flujo de trabajo tradicional: en lugar de que el usuario busque y filtre datos manualmente, el usuario hace una pregunta ("¿Quién tiene mejor % de triples, Micic o Larkin?") y la IA recupera la respuesta visualizada instantáneamente.

## 2. Problem Statement
El ecosistema de datos de la Euroliga está fragmentado. Los aficionados sofisticados (Fantasy, Apostadores) sufren fricción:
- **Inaccesibilidad:** Consultas complejas requieren SQL o no son posibles.
- **Lentitud:** Las comparaciones requieren navegar múltiples pestañas.
- **Desconexión:** Brecha entre el lenguaje natural del fan y las tablas rígidas.

## 3. Solution & Value Proposition
- **Natural Language Querying:** Motor Text-to-SQL que democratiza el acceso a los datos.
- **Visualización Generativa:** El sistema decide si mostrar una Tabla, un Bar Chart o un Line Chart según la pregunta.
- **Arquitectura Serverless:** Coste optimizado usando niveles gratuitos de Render y Neon.
- **RAG Implementado:** Sistema de Retrieval Augmented Generation sobre el esquema (no sobre los datos) para mejorar precisión en la generación de SQL. Usa OpenAI `text-embedding-3-small` para embeddings y búsqueda semántica.
- **Corrección Inteligente:** Sistema de corrección de consultas usando OpenAI para normalizar nombres de jugadores y equipos (ej: "Campazo" → "Campazzo").

## 4. Target Audience
- **Fantasy Managers:** Buscan tendencias recientes y rachas.
- **Apostadores:** Buscan "edge" en matchups específicos.
- **Hardcore Fans:** Validan argumentos en redes sociales.

## 5. Core Features (MVP) - IMPLEMENTADO ✅
- **Chat Interface:** Input de lenguaje natural tolerante a fallos con corrección automática de erratas.
- **Data Visualizer:** Renderizado condicional (Tabla/BarChart/LineChart) con Recharts.
- **Estadísticas Básicas:** Cobertura de temporada 2025 (Puntos, Rebotes, Asistencias, Triples, PIR).
- **RAG System:** Búsqueda semántica de esquema relevante para mejorar precisión de SQL (con fallback seguro).
- **Backup System:** Sistema automático de backup y recuperación de historial de chat (localStorage con migración automática).
- **Corrección Inteligente:** Normalización automática de nombres de jugadores y equipos usando OpenAI.
- **Limitaciones Actuales:** Solo temporada 2025 disponible. No se pueden consultar estadísticas por partido individual (tabla `player_game_stats` no poblada).
- **Modelo Freemium:** MVP gratuito (stats básicas de temporada 2025) con arquitectura lista para Tier Pro (stats espaciales/shot-charts).

## 6. Success Metrics
- **Time-to-Insight:** < 5 segundos desde la pregunta hasta el gráfico (objetivo cumplido en implementación actual).
- **Query Success Rate:** > 80% de consultas generan SQL válido (validado con 15+ BDD scenarios).
- **Retention:** Usuarios recurrentes tras la primera consulta (persistencia localStorage con backup automático).

## 7. Estado Actual del Proyecto
- ✅ **Fase 0:** Scaffolding & Setup (Completado)
- ✅ **Fase 1:** Data Pipeline MVP (Completado - ETL diario operativo)
- ✅ **Fase 2:** Backend & AI Engine (Completado - RAG + Text-to-SQL)
- ✅ **Fase 3:** Frontend MVP (Completado - UI completa con visualizaciones)
- 🚧 **Fase 4:** Post-MVP / Pro Features (Futuro - Multi-season, game-level stats, visualizaciones avanzadas)
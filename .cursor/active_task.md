# ðŸŽ¯ TAREA ACTIVA: ISSUE #12

## TÃ­tulo
[1.1.1] Diseño del Esquema de Base de Datos

## DescripciÃ³n y Requisitos
## Órden de Ejecución

**Tarea:** 1.1.1 (Primera tarea de la Fase 1)
**Dependencias:** Ninguna - Esta es la tarea inicial
**Bloquea a:** #13 (Modelos SQLAlchemy)

---

## Propósito

Crear el esquema inicial de la base de datos PostgreSQL con todas las tablas necesarias para almacenar datos de la Euroliga: equipos, jugadores, partidos, estadísticas y embeddings para RAG.

## Contexto y Referencias

* **Fase del Proyecto:** Fase 1.1 - Cimientos del Dominio
* **Documentación Base:** TECHNICAL_PLAN.md, SPECIFICATIONS.md

## Especificaciones de Implementación

* **Lógica:**
  - Crear archivo de migración SQL con el esquema completo
  - Incluir extensión pgvector para búsqueda vectorial
  - Definir tablas: teams, players, games, player_stats_games, schema_embeddings
  - Establecer relaciones (foreign keys) entre tablas
  - Añadir índices para optimizar consultas frecuentes

* **Dependencias:**
  - PostgreSQL con extensión pgvector
  - Neon Serverless Database

* **Restricciones:**
  - Diseño optimizado para <0.5GB (límite free tier de Neon)
  - Considerar que se usará NullPool (sin connection pooling)

## Archivos Afectados / A Crear

* [ ] backend/migrations/001_initial_schema.sql

## Criterios de Aceptación (Definition of Done)

- [ ] El archivo de migración SQL está creado y es ejecutable
- [ ] Todas las tablas definidas en TECHNICAL_PLAN.md están incluidas
- [ ] La extensión pgvector está habilitada
- [ ] Las relaciones entre tablas están correctamente definidas
- [ ] El esquema ha sido validado en una instancia local de PostgreSQL

---
## INSTRUCCIONES PARA EL AGENTE
1. Este archivo es tu FUENTE DE VERDAD para esta sesiÃ³n.
2. Implementa EXACTAMENTE lo que se pide arriba.
3. Si la issue menciona documentos, bÃºscalos en 'docs/' (o usa el resumen).
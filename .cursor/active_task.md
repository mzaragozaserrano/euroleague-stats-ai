# ðŸŽ¯ TAREA ACTIVA: ISSUE #16

## TÃ­tulo
[1.2.2] ETL Equipos

## DescripciÃ³n y Requisitos
## Órden de Ejecución

**Tarea:** 1.2.2
**Dependencias:** #15 (BDD Feature debe estar creado primero - TDD)
**Bloquea a:** #17 (BDD Jugadores)

---

## Propósito

Implementar el script ETL para ingestar datos de equipos desde la API de Euroleague a la base de datos.

## Contexto y Referencias

* **Fase del Proyecto:** Fase 1.2 - Datos Maestros
* **Documentación Base:** TECHNICAL_PLAN.md

## Especificaciones de Implementación

* **Lógica:**
  - Usar EuroleagueClient para obtener datos de equipos
  - Transformar datos de la API al formato de los modelos SQLAlchemy
  - Persistir datos usando los modelos Team
  - Implementar lógica de upsert para evitar duplicados
  - Hacer que los tests BDD pasen (Green phase de TDD)

* **Dependencias:**
  - euroleague_client.py
  - Modelos SQLAlchemy
  - Conexión a Neon DB

* **Restricciones:**
  - Los tests BDD deben pasar al finalizar
  - Manejar errores de red y base de datos

## Archivos Afectados / A Crear

* [ ] backend/etl/ingest_teams.py

## Criterios de Aceptación (Definition of Done)

- [ ] El script ETL funciona correctamente
- [ ] Los datos se persisten en la base de datos
- [ ] Los tests BDD pasan (Green phase)
- [ ] El código está refactorizado (Refactor phase)
- [ ] El código pasa el linter

---
## INSTRUCCIONES PARA EL AGENTE
1. Este archivo es tu FUENTE DE VERDAD para esta sesiÃ³n.
2. Implementa EXACTAMENTE lo que se pide arriba.
3. Si la issue menciona documentos, bÃºscalos en 'docs/' (o usa el resumen).
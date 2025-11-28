# ðŸŽ¯ TAREA ACTIVA: ISSUE #20

## TÃ­tulo
[1.3.2] ETL Partidos y Estadísticas

## DescripciÃ³n y Requisitos
## Órden de Ejecución

**Tarea:** 1.3.2 (Última tarea de la Fase 1)
**Dependencias:** #19 (BDD Feature debe estar creado primero - TDD)
**Bloquea a:** Ninguna - Esta es la tarea final de la Fase 1

---

## Propósito

Implementar el script ETL más complejo para ingestar datos de partidos y estadísticas de jugadores desde la API de Euroleague.

## Contexto y Referencias

* **Fase del Proyecto:** Fase 1.3 - Datos Transaccionales
* **Documentación Base:** TECHNICAL_PLAN.md

## Especificaciones de Implementación

* **Lógica:**
  - Usar EuroleagueClient para obtener datos de partidos
  - Obtener estadísticas (box scores) para cada partido
  - Transformar datos anidados al formato de los modelos
  - Persistir partidos y estadísticas asociadas
  - Implementar lógica de upsert para evitar duplicados
  - Manejar partidos programados vs completados
  - Hacer que los tests BDD pasen (Green phase de TDD)

* **Dependencias:**
  - euroleague_client.py
  - Modelos SQLAlchemy
  - Datos de equipos y jugadores ya ingresados

* **Restricciones:**
  - Los tests BDD deben pasar al finalizar
  - Manejar correctamente las relaciones múltiples
  - Optimizar para evitar consultas N+1

## Archivos Afectados / A Crear

* [ ] backend/etl/ingest_games.py

## Criterios de Aceptación (Definition of Done)

- [ ] El script ETL funciona correctamente con datos complejos
- [ ] Los datos se persisten con todas las relaciones
- [ ] Los tests BDD pasan (Green phase)
- [ ] El código está refactorizado (Refactor phase)
- [ ] El código pasa el linter
- [ ] El rendimiento es aceptable

---
## INSTRUCCIONES PARA EL AGENTE
1. Este archivo es tu FUENTE DE VERDAD para esta sesiÃ³n.
2. Implementa EXACTAMENTE lo que se pide arriba.
3. Si la issue menciona documentos, bÃºscalos en 'docs/' (o usa el resumen).
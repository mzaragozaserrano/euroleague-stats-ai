# ðŸŽ¯ TAREA ACTIVA: ISSUE #19

## TÃ­tulo
[1.3.1] BDD Feature - Partidos y Estadísticas

## DescripciÃ³n y Requisitos
## Órden de Ejecución

**Tarea:** 1.3.1 (Primera tarea de Sub-fase 1.3)
**Dependencias:** #12-#18 (Toda la Sub-fase 1.1 y 1.2 deben estar completas)
**Bloquea a:** #20 (ETL Partidos)

---

## Propósito

Crear el archivo de feature Gherkin para la ingesta de partidos y estadísticas de jugadores, siguiendo el flujo TDD/BDD.

## Contexto y Referencias

* **Fase del Proyecto:** Fase 1.3 - Datos Transaccionales
* **Documentación Base:** SPECIFICATIONS_GHERKIN.md

## Especificaciones de Implementación

* **Lógica:**
  - Crear archivo games.feature en backend/tests/features/
  - Definir escenarios complejos: partidos jugados vs programados
  - Incluir escenarios para estadísticas anidadas
  - Crear step definitions en backend/tests/step_defs/test_games_steps.py

* **Dependencias:**
  - pytest-bdd
  - pytest-asyncio
  - Datos de equipos y jugadores ya ingresados

* **Restricciones:**
  - Seguir sintaxis Gherkin estricta
  - Los tests deben fallar inicialmente (Red phase de TDD)
  - Manejar la complejidad de datos anidados

## Archivos Afectados / A Crear

* [ ] backend/tests/features/games.feature
* [ ] backend/tests/step_defs/test_games_steps.py

## Criterios de Aceptación (Definition of Done)

- [ ] El archivo .feature está creado con escenarios completos
- [ ] Los step definitions están generados
- [ ] Los tests ejecutan (y fallan como se espera)
- [ ] La sintaxis Gherkin es válida

---
## INSTRUCCIONES PARA EL AGENTE
1. Este archivo es tu FUENTE DE VERDAD para esta sesiÃ³n.
2. Implementa EXACTAMENTE lo que se pide arriba.
3. Si la issue menciona documentos, bÃºscalos en 'docs/' (o usa el resumen).
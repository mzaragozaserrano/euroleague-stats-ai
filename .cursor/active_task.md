# ðŸŽ¯ TAREA ACTIVA: ISSUE #17

## TÃ­tulo
[1.2.3] BDD Feature - Jugadores

## DescripciÃ³n y Requisitos
## Órden de Ejecución

**Tarea:** 1.2.3
**Dependencias:** #16 (ETL Equipos debe estar completo - los jugadores dependen de equipos)
**Bloquea a:** #18 (ETL Jugadores)

---

## Propósito

Crear el archivo de feature Gherkin para la ingesta de jugadores, siguiendo el flujo TDD/BDD.

## Contexto y Referencias

* **Fase del Proyecto:** Fase 1.2 - Datos Maestros
* **Documentación Base:** SPECIFICATIONS_GHERKIN.md

## Especificaciones de Implementación

* **Lógica:**
  - Crear archivo players.feature en backend/tests/features/
  - Definir escenarios: Given API returns players, When I run ETL, Then DB has players
  - Incluir relación con equipos
  - Crear step definitions en backend/tests/step_defs/test_players_steps.py

* **Dependencias:**
  - pytest-bdd
  - pytest-asyncio
  - Datos de equipos ya ingresados

* **Restricciones:**
  - Seguir sintaxis Gherkin estricta
  - Los tests deben fallar inicialmente (Red phase de TDD)

## Archivos Afectados / A Crear

* [ ] backend/tests/features/players.feature
* [ ] backend/tests/step_defs/test_players_steps.py

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
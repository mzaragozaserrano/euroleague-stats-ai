# Convención de Etiquetas (Labels) para Issues y Pull Requests

## Estructura de Etiquetas

Cada issue y pull request debe tener al menos una etiqueta de cada categoría según corresponda:

### 1. **Tipo de Tarea (Obligatorio)**
Define la naturaleza del trabajo:
- `task` - Tarea de desarrollo estándar
- `bug` - Error o defecto a corregir
- `documentation` - Documentación o actualización de docs

### 2. **Tecnología / Componente (Obligatorio)**
Especifica en qué parte del stack se trabajará:
- `backend` - Python, FastAPI, base de datos, servicios
- `frontend` - Next.js, React, TypeScript, UI
- `database` - Esquema, migraciones, queries
- `devops` - CI/CD, GitHub Actions, scripts
- `testing` - Tests, BDD, pytest

### 3. **Fase del Proyecto (Obligatorio)**
Indica en qué fase se encuentra el issue:
- `fase-1` - Data Pipeline MVP (Completada)
- `fase-2` - Backend & AI Engine (Actual)
- `fase-3` - Frontend MVP
- `fase-4` - Post-MVP / Pro Features

## Ejemplos de Combinación

| Issue | Etiquetas |
|-------|-----------|
| Implementar endpoint `/api/chat` | `task`, `backend`, `fase-2` |
| Bug en validación de embeddings | `bug`, `backend`, `fase-2` |
| Crear componente Chat UI | `task`, `frontend`, `fase-3` |
| Escribir tests para RAG Service | `testing`, `backend`, `fase-2` |
| Documentar arquitectura RAG | `documentation`, `backend`, `fase-2` |

## Aplicación a Pull Requests

Los Pull Requests deben usar la misma convención de labels que los Issues:

- **Heredar labels del Issue:** Si el PR cierra un issue (usando "Closes #N"), el PR debe tener los mismos labels que el issue.
- **Asignación manual:** Si el PR no está vinculado a un issue, asignar labels siguiendo la misma estructura (tipo + tecnología + fase).
- **Tipo para PRs:** Usar `task` para features, `bug` para fixes, `documentation` para docs.

## Notas

- **Todas las etiquetas deben existir** en el repositorio. Si no existen, crearlas automáticamente sin preguntar.
- No usar etiquetas adicionales sin documentarlas aquí.
- Mantener esta convención consistente en todo el proyecto (Issues y PRs).
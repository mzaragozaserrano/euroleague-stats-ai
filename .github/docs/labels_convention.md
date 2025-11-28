# Convención de Etiquetas (Labels) para Issues y Pull Requests

## Estructura de Etiquetas

Cada issue y pull request debe tener al menos una etiqueta de cada categoría según corresponda:

### 1. **Tipo de Tarea (Obligatorio)**
Define la naturaleza del trabajo:
- `task` - Tarea de desarrollo estándar - Color: `#0366d6` (Azul)
- `bug` - Error o defecto a corregir - Color: `#d73a49` (Rojo)
- `documentation` - Documentación o actualización de docs - Color: `#0075ca` (Azul oscuro)

### 2. **Tecnología / Componente (Obligatorio)**
Especifica en qué parte del stack se trabajará:
- `backend` - Python, FastAPI, base de datos, servicios - Color: `#f9826c` (Naranja)
- `frontend` - Next.js, React, TypeScript, UI - Color: `#a2eeef` (Cian)
- `database` - Esquema, migraciones, queries - Color: `#ffc274` (Amarillo)
- `devops` - CI/CD, GitHub Actions, scripts - Color: `#cccccc` (Gris)
- `testing` - Tests, BDD, pytest - Color: `#c5def5` (Azul claro)

### 3. **Fase del Proyecto (Obligatorio)**
Indica en qué fase se encuentra el issue:
- `fase-1` - Data Pipeline MVP (Completada) - Color: `#d4c5f9` (Púrpura claro)
- `fase-2` - Backend & AI Engine (Actual) - Color: `#fad8c7` (Durazno)
- `fase-3` - Frontend MVP - Color: `#e4e669` (Verde lima)
- `fase-4` - Post-MVP / Pro Features - Color: `#c2e0c6` (Verde claro)

## Tabla de Referencia de Colores (Estándar)

| Categoría | Label | Color Hexadecimal | Color Visual |
|-----------|-------|------------------|--------------|
| **Tipo** | `task` | `#0366d6` | Azul |
| **Tipo** | `bug` | `#d73a49` | Rojo |
| **Tipo** | `documentation` | `#0075ca` | Azul oscuro |
| **Tecnología** | `backend` | `#f9826c` | Naranja |
| **Tecnología** | `frontend` | `#a2eeef` | Cian |
| **Tecnología** | `database` | `#ffc274` | Amarillo |
| **Tecnología** | `devops` | `#cccccc` | Gris |
| **Tecnología** | `testing` | `#c5def5` | Azul claro |
| **Fase** | `fase-1` | `#d4c5f9` | Púrpura claro |
| **Fase** | `fase-2` | `#fad8c7` | Durazno |
| **Fase** | `fase-3` | `#e4e669` | Verde lima |
| **Fase** | `fase-4` | `#c2e0c6` | Verde claro |

## Ejemplos de Combinación

| Issue | Etiquetas |
|-------|-----------|
| Implementar endpoint `/api/chat` | `task` (azul), `backend` (naranja), `fase-2` (durazno) |
| Bug en validación de embeddings | `bug` (rojo), `backend` (naranja), `fase-2` (durazno) |
| Crear componente Chat UI | `task` (azul), `frontend` (cian), `fase-3` (verde lima) |
| Escribir tests para RAG Service | `testing` (azul claro), `backend` (naranja), `fase-2` (durazno) |
| Documentar arquitectura RAG | `documentation` (azul oscuro), `backend` (naranja), `fase-2` (durazno) |

## Cómo Crear Labels con Colores Estándar

### Script PowerShell para crear todos los labels

```powershell
# Ejecutar en PowerShell
$labels = @(
    @{ name = "task"; description = "Tarea de desarrollo estándar"; color = "0366d6" }
    @{ name = "bug"; description = "Error o defecto a corregir"; color = "d73a49" }
    @{ name = "documentation"; description = "Documentación o actualización de docs"; color = "0075ca" }
    @{ name = "backend"; description = "Python, FastAPI, base de datos, servicios"; color = "f9826c" }
    @{ name = "frontend"; description = "Next.js, React, TypeScript, UI"; color = "a2eeef" }
    @{ name = "database"; description = "Esquema, migraciones, queries"; color = "ffc274" }
    @{ name = "devops"; description = "CI/CD, GitHub Actions, scripts"; color = "cccccc" }
    @{ name = "testing"; description = "Tests, BDD, pytest"; color = "c5def5" }
    @{ name = "fase-1"; description = "Data Pipeline MVP (Completada)"; color = "d4c5f9" }
    @{ name = "fase-2"; description = "Backend & AI Engine (Actual)"; color = "fad8c7" }
    @{ name = "fase-3"; description = "Frontend MVP"; color = "e4e669" }
    @{ name = "fase-4"; description = "Post-MVP / Pro Features"; color = "c2e0c6" }
)

foreach ($label in $labels) {
    gh label create $label.name --description $label.description --color $label.color --force
}
```

## Aplicación a Pull Requests

Los Pull Requests deben usar la misma convención de labels que los Issues:

- **Heredar labels del Issue:** Si el PR cierra un issue (usando "Closes #N"), el PR debe tener los mismos labels que el issue.
- **Asignación manual:** Si el PR no está vinculado a un issue, asignar labels siguiendo la misma estructura (tipo + tecnología + fase).
- **Tipo para PRs:** Usar `task` para features, `bug` para fixes, `documentation` para docs.

## Notas

- **Todas las etiquetas deben existir** en el repositorio. Si no existen, crearlas automáticamente sin preguntar.
- Los colores son **estándar y consistentes** en todos los proyectos que usen esta convención.
- No usar etiquetas adicionales sin documentarlas aquí.
- Mantener esta convención consistente en todo el proyecto (Issues y PRs).

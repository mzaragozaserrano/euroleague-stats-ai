# Convención de Etiquetas (Labels) para Issues y Pull Requests

## Principios Generales

Las etiquetas deben ser:
1. **Categororizadas:** Agrupar por tipo, no por contenido específico
2. **Mutuamente exclusivas dentro de categoría:** Un issue debe tener máximo una etiqueta por categoría
3. **Consistentes en color:** Los mismos tipos de label siempre tienen el mismo color
4. **Opcionales pero organizadas:** Las etiquetas recomendadas siguen esta estructura

## Categorías de Etiquetas Estándar

### 1. **Tipo de Tarea**
Define la naturaleza del trabajo. Cada issue/PR debe tener máximo una.

| Label | Color | Descripción |
|-------|-------|-------------|
| `task` | `#0366d6` (Azul) | Tarea de desarrollo estándar |
| `bug` | `#d73a49` (Rojo) | Error o defecto a corregir |
| `documentation` | `#0075ca` (Azul oscuro) | Documentación o actualización de docs |
| `question` | `#d876e3` (Púrpura) | Pregunta o investigación |
| `enhancement` | `#a2eeef` (Cian) | Mejora o feature solicitada |

### 2. **Tecnología / Componente**
Especifica el área del proyecto. Cada issue/PR debe tener máximo una.

| Label | Color | Descripción |
|-------|-------|-------------|
| `backend` | `#f9826c` (Naranja) | Backend, API, servicios |
| `frontend` | `#a2eeef` (Cian) | Frontend, UI, cliente |
| `database` | `#ffc274` (Amarillo) | Base de datos, esquema, queries |
| `devops` | `#cccccc` (Gris) | CI/CD, infraestructura, scripts |
| `testing` | `#c5def5` (Azul claro) | Tests, QA, validación |

### 3. **Estado / Prioridad**
Clasifica urgencia o estado del trabajo.

| Label | Color | Descripción |
|-------|-------|-------------|
| `priority-high` | `#d73a49` (Rojo) | Alta prioridad |
| `priority-medium` | `#ffc274` (Amarillo) | Prioridad media |
| `priority-low` | `#c5def5` (Azul claro) | Baja prioridad |
| `blocked` | `#cccccc` (Gris) | Bloqueado por otra tarea |
| `in-progress` | `#f9826c` (Naranja) | Trabajo en curso |
| `review` | `#0075ca` (Azul oscuro) | En revisión |

### 4. **Otras Etiquetas Estándar de GitHub**
Etiquetas convencionales que GitHub sugiere.

| Label | Color | Descripción |
|-------|-------|-------------|
| `good first issue` | `#7057ff` (Púrpura claro) | Buena para nuevos contributores |
| `help wanted` | `#008672` (Verde) | Se busca ayuda |
| `duplicate` | `#cfd3d7` (Gris claro) | Duplicado de otro issue |
| `wontfix` | `#ffffff` (Blanco/Negro) | No será solucionado |
| `invalid` | `#e4e669` (Verde lima) | No válido o incompleto |

## Tabla de Referencia de Colores

| Color Hexadecimal | Color Visual | Uso Recomendado |
|------------------|--------------|-----------------|
| `#0366d6` | Azul | Tareas, documentación base |
| `#d73a49` | Rojo | Bugs, prioridad alta |
| `#0075ca` | Azul oscuro | Documentación, revisiones |
| `#a2eeef` | Cian | Frontend, enhancements |
| `#f9826c` | Naranja | Backend, en progreso |
| `#ffc274` | Amarillo | Database, prioridad media |
| `#cccccc` | Gris | DevOps, bloqueado |
| `#c5def5` | Azul claro | Testing, prioridad baja |
| `#7057ff` | Púrpura claro | Good first issue |
| `#008672` | Verde | Help wanted |
| `#e4e669` | Verde lima | Invalid, estado |
| `#cfd3d7` | Gris claro | Duplicado |
| `#ffffff` | Blanco/Negro | Wontfix |

## Pautas de Uso

### Para Issues

- **Asignación:** Cada issue debe tener al menos una etiqueta de "Tipo de Tarea" y opcionalmente de "Tecnología"
- **Múltiples etiquetas:** Permitir máximo una por categoría
- **Ejemplos:**
  - Issue con bug en backend: `bug` + `backend`
  - Tarea de documentación: `documentation`
  - Feature en frontend: `enhancement` + `frontend`

### Para Pull Requests

- **Heredar del Issue:** Si el PR cierra un issue, heredar sus labels
- **Si no hay issue:** Asignar labels siguiendo la misma estructura
- **Agregar estado:** Usar `in-progress`, `review` según sea necesario

## Cómo Implementar Estos Labels

### Script PowerShell genérico

```powershell
# Crear todas las etiquetas estándar
$standardLabels = @(
    # Tipo de Tarea
    @{ name = "task"; color = "0366d6"; description = "Tarea de desarrollo estándar" }
    @{ name = "bug"; color = "d73a49"; description = "Error o defecto a corregir" }
    @{ name = "documentation"; color = "0075ca"; description = "Documentación" }
    @{ name = "question"; color = "d876e3"; description = "Pregunta o investigación" }
    @{ name = "enhancement"; color = "a2eeef"; description = "Mejora o feature solicitada" }
    
    # Tecnología
    @{ name = "backend"; color = "f9826c"; description = "Backend, API, servicios" }
    @{ name = "frontend"; color = "a2eeef"; description = "Frontend, UI, cliente" }
    @{ name = "database"; color = "ffc274"; description = "Base de datos" }
    @{ name = "devops"; color = "cccccc"; description = "CI/CD, infraestructura" }
    @{ name = "testing"; color = "c5def5"; description = "Tests y QA" }
    
    # Estado/Prioridad
    @{ name = "priority-high"; color = "d73a49"; description = "Alta prioridad" }
    @{ name = "priority-medium"; color = "ffc274"; description = "Prioridad media" }
    @{ name = "priority-low"; color = "c5def5"; description = "Baja prioridad" }
    @{ name = "blocked"; color = "cccccc"; description = "Bloqueado" }
    @{ name = "in-progress"; color = "f9826c"; description = "En progreso" }
    @{ name = "review"; color = "0075ca"; description = "En revisión" }
    
    # Estándar GitHub
    @{ name = "good first issue"; color = "7057ff"; description = "Bueno para principiantes" }
    @{ name = "help wanted"; color = "008672"; description = "Se busca ayuda" }
    @{ name = "duplicate"; color = "cfd3d7"; description = "Duplicado" }
    @{ name = "wontfix"; color = "ffffff"; description = "No será solucionado" }
    @{ name = "invalid"; color = "e4e669"; description = "No válido" }
)

foreach ($label in $standardLabels) {
    gh label create $label.name --color $label.color --description $label.description --force
}

Write-Host "Labels estándar creados exitosamente"
```

## Notas

- Esta convención es **agnóstica del proyecto**. Cada proyecto puede agregar labels específicos según necesite
- Los colores son **estándar y consistentes** en todos los proyectos que usen esta convención
- Para agregar labels específicos del proyecto, crear un archivo separado: `.github/docs/PROJECT_LABELS.md`
- Los labels deben ser en minúsculas y con guiones (kebab-case): `good-first-issue`, no `Good First Issue`

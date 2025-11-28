# Labels Específicos del Proyecto

Este proyecto agrega etiquetas adicionales además de las convenciones estándar en `labels_convention.md`.

## Fases del Proyecto

Etiquetas que definen la fase de desarrollo en la que se encuentra el work.

| Label | Color | Descripción |
|-------|-------|-------------|
| `fase-1` | `#d4c5f9` (Púrpura claro) | Data Pipeline MVP (Completada) |
| `fase-2` | `#fad8c7` (Durazno) | Backend & AI Engine (Actual) |
| `fase-3` | `#e4e669` (Verde lima) | Frontend MVP |
| `fase-4` | `#c2e0c6` (Verde claro) | Post-MVP / Pro Features |

## Uso Recomendado

Cada issue/PR **debe tener exactamente una etiqueta de fase** que indique en qué momento del proyecto se realiza el trabajo.

### Ejemplos de Combinaciones

| Issue | Etiquetas |
|-------|-----------|
| Implementar endpoint `/api/chat` | `task`, `backend`, `fase-2` |
| Bug en validación de embeddings | `bug`, `backend`, `fase-2` |
| Crear componente Chat UI | `task`, `frontend`, `fase-3` |
| Escribir tests para RAG Service | `testing`, `backend`, `fase-2` |
| Documentar arquitectura RAG | `documentation`, `backend`, `fase-2` |

## Crear Labels de Fase

```powershell
# Crear etiquetas de fase específicas del proyecto
$phaseLabels = @(
    @{ name = "fase-1"; color = "d4c5f9"; description = "Data Pipeline MVP (Completada)" }
    @{ name = "fase-2"; color = "fad8c7"; description = "Backend & AI Engine (Actual)" }
    @{ name = "fase-3"; color = "e4e669"; description = "Frontend MVP" }
    @{ name = "fase-4"; color = "c2e0c6"; description = "Post-MVP / Pro Features" }
)

foreach ($label in $phaseLabels) {
    gh label create $label.name --color $label.color --description $label.description --force
}

Write-Host "Labels de fase creados exitosamente"
```

## Notas

- Los labels de fase **son opcionales** para otros proyectos
- Si tu proyecto tiene un ciclo diferente, ajusta las fases según sea necesario
- La convención estándar en `labels_convention.md` es el punto de partida obligatorio


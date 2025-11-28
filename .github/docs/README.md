# Documentación GitHub & Convenciones

Esta carpeta contiene la documentación y convenciones que rigen el flujo de trabajo del proyecto.

## Archivos Principales

### 1. **labels_convention.md** (Genérico - Reutilizable)
Convención estándar de etiquetas para GitHub que es **agnóstica del proyecto**.

Define:
- Categorías de labels (Tipo de Tarea, Tecnología, Estado/Prioridad)
- Tabla de colores estándar y consistentes
- Guías de uso
- Script PowerShell genérico para crear todos los labels

**Uso:** Aplicable a cualquier proyecto. Es el punto de partida.

### 2. **PROJECT_LABELS.md** (Específico - Este Proyecto)
Etiquetas y convenciones **específicas de este proyecto**.

Define:
- Labels adicionales (ej: fases del proyecto)
- Combinaciones específicas de labels para este proyecto
- Instrucciones de creación

**Uso:** Solo para este proyecto. Extiende la convención estándar.

### 3. **windows_utf8_setup.md** (Específico - Para Windows)
Guía de manejo de UTF-8 y caracteres especiales en PowerShell en Windows.

Define:
- Reglas de sintaxis para Git vs GitHub CLI
- Tabla de referencia Unicode
- Ejemplos prácticos

**Uso:** Cuando trabajes con scripts PowerShell en Windows.

## Estructura de Carpetas

```
.github/
├── docs/                           # Esta carpeta
│   ├── README.md                   # Este archivo
│   ├── labels_convention.md        # Convención genérica de labels
│   ├── PROJECT_LABELS.md           # Labels específicos del proyecto
│   └── windows_utf8_setup.md       # Guía UTF-8 para Windows
│
├── scripts/
│   ├── Setup-StandardLabels.ps1    # Crear labels estándar (genérico)
│   ├── New-BatchIssues.ps1         # Crear issues en lote
│   ├── New-BatchPRs.ps1            # Crear PRs en lote
│   └── Enable-Utf8.ps1             # Configurar UTF-8 en PowerShell
│
└── workflows/                      # (No crear aquí - ver .cursor/workflows/)
```

## Flujo Recomendado

### Para Usar este Proyecto

1. **Primera vez:**
   ```powershell
   powershell -File .github/scripts/Setup-StandardLabels.ps1
   ```

2. **Crear issues:**
   - Consultar `PROJECT_LABELS.md` para asignar labels correctos
   - Usar `.cursor/workflows/feature-workflow.md` para features
   - Usar `.cursor/workflows/bug-workflow.md` para bugs

3. **Crear PRs:**
   - Heredar labels del issue vinculado
   - Seguir convención en `labels_convention.md`

### Para Crear un Nuevo Proyecto

1. Copiar `labels_convention.md` (es genérico)
2. Copiar `windows_utf8_setup.md` si usas Windows
3. Copiar `.github/scripts/Setup-StandardLabels.ps1` (es genérico)
4. Crear tu propio `PROJECT_LABELS.md` con labels específicos
5. Ejecutar `Setup-StandardLabels.ps1`

## Actualizaciones Futuras

### Si Necesitas Nuevos Labels Genéricos

Editar `labels_convention.md` y agregar nuevas categorías o colores. Luego:
```powershell
powershell -File .github/scripts/Setup-StandardLabels.ps1
```

### Si Necesitas Labels Específicos del Proyecto

Editar `PROJECT_LABELS.md` y crear los nuevos labels manualmente:
```powershell
gh label create tu-nuevo-label --color XXXXXX --description "Descripción"
```

## Referencias

- **GitHub API:** https://docs.github.com/en/rest/issues/labels
- **Buenas Prácticas:** https://gist.github.com/borekb/d61cdc45f0c92606a92b15388cf80185
- **Convención Commits:** https://www.conventionalcommits.org/

## Notas

- Los colores en `labels_convention.md` son **estándares** y deben mantenerse consistentes
- Los labels en `PROJECT_LABELS.md` pueden variar según el proyecto
- Ambos documentos tienen scripts PowerShell listos para usar


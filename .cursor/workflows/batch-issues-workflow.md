# Batch Issue Creation Workflow

**Trigger:** User commands "BATCH PHASE <PHASE_NUMBER>" (e.g., "BATCH PHASE 2")
**Pre-requisites:** `gh` CLI installed. `docs/roadmap.md` exists.

## Step 1: Validar/Crear project_labels.json

**IMPORTANTE:** Este paso verifica que existe la configuración de etiquetas.

1. Verificar que existe `.github/docs/project_labels.json`
   - **Si NO existe:** 
     - **EJECUTAR:** `.\.github\scripts\Sync-ProjectLabels.ps1`
     - El script creará el archivo automáticamente con la configuración por defecto basada en `labels_convention.md`
     - **Y automáticamente ejecutará la sincronización** para crear las etiquetas en GitHub
   - **Si YA existe:** 
     - **NO ejecutar** el script de sincronización
     - Solo usar el archivo para consultar las etiquetas disponibles en los siguientes pasos

**Nota:** El usuario puede ejecutar manualmente la sincronización cuando lo desee:
```powershell
.\.github\scripts\Sync-ProjectLabels.ps1
```

## Step 2: Roadmap Analysis
1. Read `@docs/roadmap.md`.
2. Locate the section corresponding to the requested Phase.
3. Extract all unchecked tasks (`- [ ]`) from that phase.
4. If a task has sub-tasks (indented), treat the parent as an "Epic" (or main issue) and sub-tasks as details in the Body, OR split them into separate issues if they are complex.

## Step 4: Update Automation Script
You must update the content of the `$issues` array inside `.github/scripts/New-BatchIssues.ps1`.

**Instructions for the Agent (LOCAL PowerShell Context):**
1. **ENCODING CHECK (CRITICAL):** You are running on Windows PowerShell locally. However, this script uses `gh cli` which handles UTF-8 natively.
2. **Consult References:** 
   - Read `.github/docs/windows_utf8_setup.md` for context.
   - Read `.github/docs/project_labels.json` to determine correct labels (fuente de verdad basada en `labels_convention.md`).
3. **String Format (RECOMMENDED - Here-Strings):** Use Here-Strings (@"..."@) for `Title` and `Body`. You can write tildes directly - `gh cli` handles them.
   - ✅ **PREFERRED:** `Title = @"Opción de Menú"@` (tildes direct, Here-String)
   - ⚠️ **ALTERNATIVE:** `Title = "Opción de Menú"` (raw tildes, may work but less safe)
   - ❌ **AVOID:** `Title = "Opci$([char]0x00F3)n de Men$([char]0x00FA)"` (verboso e innecesario here)
4. **Assign Labels:** For each issue, assign labels following the convention:
   - **Type:** `task`, `bug`, or `documentation`
   - **Technology:** `backend`, `frontend`, `database`, `devops`, or `testing`
   - **Phase:** `fase-1`, `fase-2`, `fase-3`, or `fase-4` (based on the roadmap phase)
   - Format in script: `Labels = "task,backend,fase-2"` (comma-separated, no spaces)

**Example of code to inject:**
```powershell
$issues = @(
    # Using Here-Strings with direct tildes (RECOMMENDED)
    @{ 
        Title = @"UI: Botón de Pánico"@
        Body = @"
Crear acción rápida para detener el proceso.
        "@
        Labels = "task,frontend,fase-3" 
    }
)
```

## Step 6: User Confirmation
1. Show the user the list of titles you are about to create.
2. **STOP** and ask: "Do these issues look correct? Should I execute the script?"

## Step 7: Execution (PowerShell)
Once confirmed, execute the script to push issues to GitHub:

```powershell
.\.github\scripts\New-BatchIssues.ps1
```

## Step 8: Documentation Update
1. Update `@docs/active_context.md`:
   - Note that Phase <X> has started.
   - List the newly created issues (if possible, ask user to run `gh issue list` to get IDs, otherwise just note the batch creation).
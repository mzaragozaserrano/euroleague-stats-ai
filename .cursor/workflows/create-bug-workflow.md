# Report Bug Workflow

**Trigger:** User commands "REPORT BUG <TITLE>" or just "BUG <TITLE>"
**Pre-requisites:** `gh` CLI installed.

## Step 1: Information Gathering
The agent must ensure the bug report is complete.
1. **Analyze the request.** If the user only provided a title, ASK for:
   - **Description:** What is happening?
   - **Reproduction Steps:** How can we trigger it?
   - **Context:** Browser/OS or specific Situation ID (if applicable).
   
   *Wait for user response before proceeding.*

## Step 2: Content Preparation & Sanitization
**Context: LOCAL PowerShell + gh cli (which handles UTF-8 natively)**
1. **Consult References:** 
   - Read `.github/docs/windows_utf8_setup.md` for context.
   - Read `.github/docs/labels_convention.md` for label structure.
2. **Prepare Strings:** Use Here-Strings (@"..."@) for title and body. Write tildes directly - `gh cli` handles them.
   - Example: @"Error en validación"@ (tildes work fine - no subexpressions needed)
3. **Determine Labels:** Based on the bug context, assign labels following the convention:
   - **Type:** `bug` (mandatory for bugs)
   - **Technology:** `backend`, `frontend`, `database`, `devops`, or `testing`
   - **Phase:** `fase-1`, `fase-2`, `fase-3`, or `fase-4` (check `docs/roadmap.md` for current phase)

## Step 3: Execution (PowerShell)
Construct the command to create the issue with the appropriate labels using Here-Strings.
*Note: Replace `<TITLE>`, `<BODY>`, and `<LABELS>` with the actual strings. Labels format: "bug,backend,fase-2" (comma-separated).*

```powershell
# Use Here-Strings (@"..."@) for multi-line bodies with tildes
# gh cli handles UTF-8 internally on Windows - no subexpressions needed
$Title = @"Error en validación de entrada"@
$Body = @"
## Descripción
Describe el error aquí.

## Pasos para reproducir
1. Paso uno
2. Paso dos

## Contexto
Sistema operativo: Windows
Navegador: Chrome
"@
$Labels = "bug,backend,fase-2"

gh issue create --title "$Title" --body "$Body" --label "$Labels";
# Note: If labels don't exist, GitHub CLI will create them automatically.
# Here-Strings + gh cli = UTF-8 works seamlessly on Windows.
```

## Step 4: Documentation Update
1. Update `@docs/active_context.md`:
   - Mention that a new bug has been reported (include the Issue URL or ID returned by the command).
   - Ask the user if they want to switch context to fix it immediately ("FIX #<ID>").
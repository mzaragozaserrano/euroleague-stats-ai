# Batch Issue Creation Workflow

**Trigger:** User commands "BATCH PHASE <PHASE_NUMBER>" (e.g., "BATCH PHASE 2")
**Pre-requisites:** `gh` CLI installed. `docs/roadmap.md` exists.

## Step 1: Roadmap Analysis
1. Read `@docs/roadmap.md`.
2. Locate the section corresponding to the requested Phase.
3. Extract all unchecked tasks (`- [ ]`) from that phase.
4. If a task has sub-tasks (indented), treat the parent as an "Epic" (or main issue) and sub-tasks as details in the Body, OR split them into separate issues if they are complex.

## Step 2: Update Automation Script
You must update the content of the `$issues` array inside `.github/scripts/New-BatchIssues.ps1`.

**Instructions for the Agent:**
1. **ENCODING CHECK (CRITICAL):** You are running on Windows PowerShell. You MUST NOT use raw special characters (ñ, á, é, etc.).
2. **Consult Reference:** Read `.github/docs/WINDOWS_UTF8_SETUP.md` to get the hex codes.
3. **Sanitize Strings:** Replace every special character in `Title` and `Body` with its subexpression equivalent (e.g., `$([char]0x00F3)` for `ó`).
   - ❌ "Opción de Menú"
   - ✅ "Opci$([char]0x00F3)n de Men$([char]0x00FA)"

**Example of code to inject:**
```powershell
$issues = @(
    @{ Title = "UI: Bot$([char]0x00F3)n de P$([char]0x00E1)nico"; Body = "Crear acci$([char]0x00F3)n r$([char]0x00E1)pida..."; Labels = "feat, phase-2" }
)
```

## Step 3: User Confirmation
1. Show the user the list of titles you are about to create.
2. **STOP** and ask: "Do these issues look correct? Should I execute the script?"

## Step 4: Execution (PowerShell)
Once confirmed, execute the script to push issues to GitHub:

```powershell
.\.github\scripts\New-BatchIssues.ps1
```

## Step 5: Documentation Update
1. Update `@docs/active_context.md`:
   - Note that Phase <X> has started.
   - List the newly created issues (if possible, ask user to run `gh issue list` to get IDs, otherwise just note the batch creation).
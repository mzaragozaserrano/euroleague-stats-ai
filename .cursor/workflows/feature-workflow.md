# Feature Start Workflow

**Trigger:** User commands "START #<ISSUE_NUMBER>"
**Pre-requisites:** `gh` CLI installed and authenticated.

## Step 1: Context Gathering
1. Read the issue details using `gh issue view <ISSUE_NUMBER>`.
2. Analyze `@docs/architecture.md` and `@docs/project_brief.md` to understand the impact.

## Step 2: Branch Creation (PowerShell)
Execute the following commands strictly in the terminal.
*Note: Replace `<ISSUE_NUMBER>` with the actual ID and `<SLUG>` with a short, kebab-case description.*

```powershell
git checkout main;
git pull origin main;
$issueId = "<ISSUE_NUMBER>";
$desc = "<SLUG>"; 
# Example: "feat/issue-42-fix-login"
git checkout -b "feat/issue-$issueId-$desc";
```

## Step 3: Documentation Update & Initial Commit
1. Update `@docs/active_context.md`:
   - Set "Current Focus" to the Issue Title.
   - Add the Issue ID to "Active Problems" or "Recent Decisions".
2. **Execute immediately** (Apply UTF-8 rules from `.github/docs/windows_utf8_setup.md` for the message):
   - **CRITICAL:** Use subexpressions `$([char]0x00XX)` for any special characters in commit messages (local PowerShell).
   - Here-Strings are NOT recommended for `git commit -m` on Windows.

```powershell
git add docs/active_context.md;
git commit -m "chore(docs): start work on issue #<ISSUE_NUMBER>";
git push -u origin HEAD;
```

## Step 4: Create Linked Pull Request
Create a Pull Request with appropriate labels.
**CRITICAL - Context Matters (LOCAL PowerShell):** 
1. Use Here-Strings (@"..."@) for title and body - `gh cli` handles UTF-8 internally.
2. Read the issue labels using `gh issue view <ISSUE_NUMBER> --json labels` to inherit them, or assign labels following `.github/docs/labels_convention.md`.
3. **MANDATORY:** Define variables in separate lines - NEVER chain here-strings with `;` in a single line.
4. **NEVER omit special characters (tildes, ñ, etc.)** - If syntax fails, fix the syntax, don't simplify the text.
ll
# ✅ CORRECT: Define variables separately with here-strings
$issueLabels = (gh issue view <ISSUE_NUMBER> --json labels | ConvertFrom-Json).labels.name -join ","

$prTitle = @"feat: implementación de búsqueda"@

$prBody = @"
Descripción completa con tildes y caracteres especiales.

## Tareas:
- Implementar funcionalidad
- Validar con tests
- Documentar cambios

Closes #<ISSUE_NUMBER>
"@

gh pr create --title $prTitle --body $prBody --label "$issueLabels"

# ❌ INCORRECT: Chaining here-strings in one line (breaks syntax)
gh pr create --title @"..."@ --body @"..."@ --label "..."  # DON'T DO THIS

# ❌ INCORRECT: Omitting special characters as workaround
gh pr create --title "feat: implementacion" --body "Sin tildes"  # NEVER DO THIS**Key Rules:**
- **Always use here-strings** (`@"..."@`) for PR titles/bodies with special characters
- **Define variables separately** - one command per variable assignment
- **If syntax fails, fix the syntax** - never remove special characters as a workaround
- **Test the variable** with `Write-Host $prBody` before using it if unsure

## Step 5: Execution Plan
1. Propose a mini-plan of 3-4 steps to solve the issue.
2. Ask the user for confirmation before writing the actual feature code.
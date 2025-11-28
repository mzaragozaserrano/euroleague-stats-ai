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

```powershell
git add docs/active_context.md;
git commit -m "chore(docs): start work on issue #<ISSUE_NUMBER>";
git push -u origin HEAD;
```

## Step 4: Create Linked Pull Request
Create a Draft PR with appropriate labels.
**CRITICAL:** 
1. Use Here-Strings (@"..."@) for title and body - this handles tildes automatically.
2. Read the issue labels using `gh issue view <ISSUE_NUMBER> --json labels` to inherit them, or assign labels following `.github/docs/labels_convention.md`.

```powershell
# Get issue labels to inherit them
$issueLabels = (gh issue view <ISSUE_NUMBER> --json labels | ConvertFrom-Json).labels.name -join ","
# If no labels found, assign based on convention: "task,backend,fase-2" (check docs/roadmap.md for phase)
# Example with Here-String (supports tildes directly):
gh pr create --draft --title @"feat: implementación de búsqueda"@ --body @"Work in progress. Closes #<ISSUE_NUMBER>"@ --label "$issueLabels";
# Note: Here-Strings (@"..."@) automatically handle UTF-8 and tildes. No need for $([char]0x00XX) escaping.
```

## Step 5: Execution Plan
1. Propose a mini-plan of 3-4 steps to solve the issue.
2. Ask the user for confirmation before writing the actual feature code.
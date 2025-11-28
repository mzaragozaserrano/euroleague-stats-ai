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
Create a Draft PR.
**CRITICAL:** Sanitize the title and body using `.github/docs/windows_utf8_setup.md`.

```powershell
# Example Title: "feat: validaci$([char]0x00F3)n de l$([char]0x00F3)gica"
gh pr create --draft --title "<TYPE>: <SANITIZED_TITLE>" --body "Work in progress. Closes #<ISSUE_NUMBER>";
```

## Step 5: Execution Plan
1. Propose a mini-plan of 3-4 steps to solve the issue.
2. Ask the user for confirmation before writing the actual feature code.
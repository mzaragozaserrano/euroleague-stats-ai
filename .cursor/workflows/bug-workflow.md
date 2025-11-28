# Bug Fix Workflow

**Trigger:** User commands "FIX #<ISSUE_NUMBER>"
**Pre-requisites:** `gh` CLI installed.

## Step 1: Diagnosis & Context
1. Read the issue details: `gh issue view <ISSUE_NUMBER>`.
2. Analyze `@docs/architecture.md` and `@docs/active_context.md` to understand the broken area.
3. **CRITICAL:** Before fixing, ask the user: "Do we have a reproduction case or a failing test? Should I create one?"

## Step 2: Branch Creation (PowerShell)
Standard bugfix naming convention.
*Replace `<ISSUE_NUMBER>` and `<SLUG>` (short description).*

```powershell
git checkout main;
git pull origin main;
$issueId = "<ISSUE_NUMBER>";
$desc = "<SLUG>"; 
# Example: "fix/issue-42-grid-selection-error"
git checkout -b "fix/issue-$issueId-$desc";
```

## Step 3: Documentation Update & Initial Commit
1. Update `@docs/active_context.md`:
   - Add the Issue ID and description to the **"Active Problems / Blockers"** section.
   - Set "Current Focus" to "Debugging Issue #<ID>".
2. **Execute immediately** (Apply UTF-8 rules from `.github/docs/windows_utf8_setup.md`):

```powershell
git add docs/active_context.md;
# Example: "chore(docs): start debugging issue..."
git commit -m "chore(docs): start debugging issue #<ISSUE_NUMBER>";
git push -u origin HEAD;
```

## Step 4: Create Draft Pull Request
Create a PR to track the fix.
**CRITICAL:** Sanitize the title using `.github/docs/windows_utf8_setup.md`.

```powershell
# Title Example: "fix: correcci$([char]0x00F3)n del timer"
gh pr create --draft --title "fix: <SANITIZED_TITLE>" --body "Investigating bug. Closes #<ISSUE_NUMBER>";
```

## Step 5: Execution Loop
1. **Reproduce:** Create a failing test case (if applicable) that proves the bug exists.
2. **Fix:** Modify the code to pass the test.
3. **Verify:** Run full test suite to ensure no regressions.
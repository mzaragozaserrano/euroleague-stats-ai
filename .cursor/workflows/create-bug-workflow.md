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
**CRITICAL:** You are running on Windows PowerShell.
1. **Consult Reference:** Read `.github/docs/windows_utf8_setup.md`.
2. **Sanitize Strings:** Prepare the Title and Body variables replacing special characters with subexpressions.
   - Example: "Error en validación" -> "Error en validaci$([char]0x00F3)n"

## Step 3: Execution (PowerShell)
Construct the command to create the issue with the `bug` label.
*Note: Replace `<TITLE>` and `<BODY>` with the sanitized strings.*

```powershell
$Title = "<SANITIZED_TITLE>";
$Body = "<SANITIZED_BODY_MARKDOWN>";
# We use a Here-String for the body to support multi-line if needed, 
# but ensure to escape internal quotes if passing directly to the flag.
# A safer approach for complex bodies involves a temporary file, but for simple reports:

gh issue create --title "$Title" --body "$Body" --label "bug";
```

## Step 4: Documentation Update
1. Update `@docs/active_context.md`:
   - Mention that a new bug has been reported (include the Issue URL or ID returned by the command).
   - Ask the user if they want to switch context to fix it immediately ("FIX #<ID>").
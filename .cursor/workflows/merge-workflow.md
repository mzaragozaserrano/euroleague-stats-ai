# Workflow de Merge y Cierre de Tarea (Cleanup)

Este documento es una lista de control ejecutable para cerrar el ciclo de una tarea. Úsalo cuando la PR haya sido aprobada y esté lista para integrarse.

## 0. Pre-condiciones
- [ ] Identifica el número de Issue (ID) asociado a la tarea actual (ej: #4).
- [ ] Asegúrate de estar situado en la rama de la feature que quieres mergear.
- [ ] Verifica que la PR ha sido aprobada (si es un requisito del repo).

## 1. Fusión de la Pull Request (Remote)
- [ ] **Merge y Borrado Remoto:** Fusiona la PR actual y elimina la rama en GitHub automáticamente:
    * Ejecuta: `gh pr merge --merge --delete-branch`
    * *Nota:* Si pregunta confirmación, acepta.

## 2. Actualización de la Issue Actual
- [ ] **Etiquetado:** Actualiza el estado visual de la issue:
    * Ejecuta: `gh issue edit <NUMERO_ISSUE> --remove-label "needs review" --add-label "done"`
    * Adapta los nombres de los labels según tu proyecto (ej: "in-progress", "completed", etc.)
- [ ] **Cierre:** Cierra la issue de la tarea actual formalmente:
    * Ejecuta: `gh issue close <NUMERO_ISSUE>`
    * *Nota:* SOLO se cierra la issue de la tarea actual, NO las issues referenciadas en la PR.
    * Si la PR usó "Closes #<NUMERO_ISSUE>", la issue se cerrará automáticamente.

## 3. Limpieza Local
- [ ] **Vuelta a Base:**
    ```bash
    git checkout main
    git pull
    ```
- [ ] **Borrado Rama Local:**
    ```bash
    git branch -d feat/issue-<ID>
    ```
    *(Usa `-D` mayúscula si se queja).*
- [ ] **Limpieza de Contexto:**
    ```powershell
    Remove-Item .cursor/active_task.md -ErrorAction SilentlyContinue
    ```

## 4. Actualización de Referencias (Solo lo vital)
- [ ] **Roadmap:** Marca la tarea como `[x]` en `docs/ROADMAP.md` (o tu plan activo).
- [ ] **AI Summary:** Si hubo cambios arquitectónicos, actualiza `docs/AI_CONTEXT.md`.
- [ ] **Commit de Mantenimiento (Opcional):**
    ```bash
    git add docs/
    git commit -m "docs: update roadmap for #<ID>"
    git push
    ```

## 5. Verificación Final
- [ ] Comprueba que estás en la rama base (ej: `main`, `master`, `develop`).
- [ ] Comprueba que `git status` está limpio.
- [ ] Verifica que la documentación fue actualizada y pusheada.
- [ ] Confirma al usuario que la tarea <NUMERO_ISSUE> ha sido completada y archivada.

# Workflow de Implementación

## 1. Anclaje de Contexto (CRÍTICO)
- [ ] **Descargar Tarea:** Ejecuta el script para fijar el objetivo (Sustituye `<ID>` por el número):
    ```powershell
    .github/scripts/Get-TaskContext.ps1 -IssueNumber <ID>
    ```
- [ ] **LEER OBJETIVO:** Abre y lee el archivo generado `.cursor/active_task.md`. **Esa es tu instrucción maestra.**

## 2. Preparación
- [ ] **UTF-8:** Ejecutar `.github/scripts/Enable-Utf8.ps1`.
- [ ] **Sincronización:**
    ```bash
    git checkout main
    git pull
    git checkout -b feat/issue-<ID>
    ```
- [ ] **Estado:**
    ```bash
    gh issue edit <ID> --add-label "in progress"
    ```

## 3. Desarrollo (Basado en `.cursor/active_task.md`)
- [ ] Implementar cambios siguiendo las instrucciones del archivo descargado.
- [ ] **NO Backend:** Usar Dexie.js para datos.
- [ ] Consultar referencias en `@05_AI_SUMMARY.md` si es necesario.

## 4. Calidad (Stop on Error)
- [ ] `npm run lint`
- [ ] `npx tsc --noEmit`
- [ ] `npm test`

## 5. Entrega
- [ ] **Commit:**
    ```bash
    git add .
    git commit -m "feat(issue-<ID>): implement task details"
    ```
    *(Ver `WINDOWS_UTF8_SETUP.md` para tildes)*.
- [ ] **Push:** `git push -u origin HEAD`
- [ ] **PR:** Edita y ejecuta `.github/scripts/New-PullRequest.ps1`